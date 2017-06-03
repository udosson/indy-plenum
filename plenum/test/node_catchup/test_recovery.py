from time import perf_counter

import pytest

from plenum.common.constants import DOMAIN_LEDGER_ID, LedgerState
from plenum.common.util import updateNamedTuple
from plenum.test.delayers import cqDelay, cr_delay
from plenum.test.test_client import TestClient
from stp_zmq.zstack import KITZStack

from stp_core.loop.eventually import eventually
from plenum.common.types import HA
from stp_core.common.log import getlogger
from plenum.test.helper import sendReqsToNodesAndVerifySuffReplies
from plenum.test.node_catchup.helper import waitNodeDataEquality, \
    check_ledger_state
from plenum.test.pool_transactions.helper import disconnect_node_and_ensure_disconnected, \
    buildPoolClientAndWallet
from plenum.test.test_ledger_manager import TestLedgerManager
from plenum.test.test_node import checkNodesConnected, TestNode
from plenum.test import waits

# Do not remove the next import
from plenum.test.node_catchup.conftest import whitelist

logger = getlogger()
txnCount = 5


@pytest.fixture(scope="function", autouse=True)
def limitTestRunningTime():
    # remove general limit for this module
    return None


def testNodeCatchupAfterRestart(newNodeCaughtUp, txnPoolNodeSet, tconf,
                                nodeSetWithNodeAddedAfterSomeTxns,
                                tdirWithPoolTxns, allPluginsPath,
                                poolTxnStewardData):
    """
    A node that restarts after some transactions should eventually get the
    transactions which happened while it was down
    :return:
    """
    looper, newNode, client, wallet, _, _ = nodeSetWithNodeAddedAfterSomeTxns
    logger.debug("Stopping node {} with pool ledger size {}".
                 format(newNode, newNode.poolManager.txnSeqNo))
    disconnect_node_and_ensure_disconnected(looper, txnPoolNodeSet, newNode)
    looper.removeProdable(newNode)
    # TODO: Check if the node has really stopped processing requests?
    logger.debug("Sending requests")

    # Here's where we apply some load
    for i in range(100):
        # c, w = buildPoolClientAndWallet(poolTxnStewardData,
        #                                           tdirWithPoolTxns,
        #                                           clientClass=TestClient)
        # looper.add(c)
        # sendReqsToNodesAndVerifySuffReplies(looper, w, c, 5)
        sendReqsToNodesAndVerifySuffReplies(looper, wallet, client, 5)
        # looper.removeProdable(c)

    logger.debug("Starting the stopped node, {}".format(newNode))
    nodeHa, nodeCHa = HA(*newNode.nodestack.ha), HA(*newNode.clientstack.ha)
    newNode = TestNode(newNode.name, basedirpath=tdirWithPoolTxns, config=tconf,
                       ha=nodeHa, cliha=nodeCHa, pluginPaths=allPluginsPath)
    looper.add(newNode)
    txnPoolNodeSet[-1] = newNode

    # Delay catchup reply processing so LedgerState does not change
    delay_catchup_reply = 5
    newNode.nodeIbStasher.delay(cr_delay(delay_catchup_reply))
    looper.run(checkNodesConnected(txnPoolNodeSet))

    # Make sure ledger starts syncing (sufficient consistency proofs received)
    looper.run(eventually(check_ledger_state, newNode, DOMAIN_LEDGER_ID,
                          LedgerState.syncing, retryWait=.5, timeout=5))

    # Not accurate timeout but a conservative one
    timeout = waits.expectedPoolGetReadyTimeout(len(txnPoolNodeSet)) + \
              2*delay_catchup_reply
    waitNodeDataEquality(looper, newNode, *txnPoolNodeSet[:4],
                         customTimeout=timeout)

    sendReqsToNodesAndVerifySuffReplies(looper, wallet, client, 5)
    waitNodeDataEquality(looper, newNode, *txnPoolNodeSet[:4], customTimeout=timeout)


