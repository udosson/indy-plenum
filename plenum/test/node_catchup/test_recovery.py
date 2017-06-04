import logging
from statistics import pstdev, mean
from time import perf_counter
from types import MethodType

import pytest

from plenum.common.constants import DOMAIN_LEDGER_ID, LedgerState
from plenum.test.delayers import cr_delay
from plenum.test.test_client import TestClient

from stp_core.loop.eventually import eventually
from plenum.common.types import HA
from stp_core.common.log import getlogger, Logger, DISPLAY_LOG_LEVEL
from plenum.test.helper import sendReqsToNodesAndVerifySuffReplies
from plenum.test.node_catchup.helper import waitNodeDataEquality, \
    check_ledger_state
from plenum.test.pool_transactions.helper import \
    disconnect_node_and_ensure_disconnected, buildPoolClientAndWallet
from plenum.test.test_node import checkNodesConnected, TestNode
from plenum.test import waits

# noinspection PyUnresolvedReferences
from plenum.test.node_catchup.conftest import whitelist

# Logger.setLogLevel(logging.WARNING)
logger = getlogger()
txnCount = 5


@pytest.fixture(scope="function", autouse=True)
def limitTestRunningTime():
    # remove general limit for this module
    return None


def test_node_load(looper, txnPoolNodeSet, tconf,
                   tdirWithPoolTxns, allPluginsPath,
                   poolTxnStewardData, capsys):
    client, wallet = buildPoolClientAndWallet(poolTxnStewardData,
                                              tdirWithPoolTxns,
                                              clientClass=TestClient)
    looper.add(client)
    looper.run(client.ensureConnectedToNodes())

    client_batches = 150
    txns_per_batch = 25
    for i in range(client_batches):
        s = perf_counter()
        sendReqsToNodesAndVerifySuffReplies(looper, wallet, client,
                                            txns_per_batch,
                                            override_timeout_limit=True)
        with capsys.disabled():
            print('{} executed {} client txns in {:.2f} seconds'.
                  format(i + 1, txns_per_batch, perf_counter() - s))


# This is failing because the time to process txns is steadily increasing
# https://gist.github.com/jasonalaw/117624a020e3e755826be23204a630be
def test_node_load_consistent_time(looper, txnPoolNodeSet, tconf,
                                   tdirWithPoolTxns, allPluginsPath,
                                   poolTxnStewardData, capsys):
    client, wallet = buildPoolClientAndWallet(poolTxnStewardData,
                                              tdirWithPoolTxns,
                                              clientClass=TestClient)
    looper.add(client)
    looper.run(client.ensureConnectedToNodes())

    client_batches = 300
    txns_per_batch = 25
    time_log = []
    for i in range(client_batches):
        s = perf_counter()
        sendReqsToNodesAndVerifySuffReplies(looper, wallet, client,
                                            txns_per_batch,
                                            override_timeout_limit=True)
        t = perf_counter() - s
        if len(time_log) >= 3:
            m = mean(time_log)
            sd = pstdev(time_log)
            assert abs(t - m) <= sd
        time_log.append(t)
        with capsys.disabled():
            print('{} executed {} client txns in {:.2f} seconds'.
                  format(i + 1, txns_per_batch, t))


def test_node_load_after_add(newNodeCaughtUp, txnPoolNodeSet, tconf,
                             nodeSetWithNodeAddedAfterSomeTxns,
                             tdirWithPoolTxns, allPluginsPath,
                             poolTxnStewardData, capsys):
    """
    A node that restarts after some transactions should eventually get the
    transactions which happened while it was down
    :return:
    """
    looper, newNode, client, wallet, _, _ = nodeSetWithNodeAddedAfterSomeTxns
    # logger.debug("Stopping node {} with pool ledger size {}".
    #              format(newNode, newNode.poolManager.txnSeqNo))
    # disconnect_node_and_ensure_disconnected(looper, txnPoolNodeSet, newNode)
    # looper.removeProdable(newNode)
    # TODO: Check if the node has really stopped processing requests?
    logger.debug("Sending requests")

    # Here's where we apply some load
    client_batches = 300
    txns_per_batch = 25
    for i in range(client_batches):
        s = perf_counter()
        sendReqsToNodesAndVerifySuffReplies(looper, wallet, client,
                                            txns_per_batch,
                                            override_timeout_limit=True)
        with capsys.disabled():
            print('{} executed {} client txns in {:.2f} seconds'.
                  format(i+1, txns_per_batch, perf_counter()-s))

    logger.debug("Starting the stopped node, {}".format(newNode))
    nodeHa, nodeCHa = HA(*newNode.nodestack.ha), HA(*newNode.clientstack.ha)
    # newNode = TestNode(newNode.name, basedirpath=tdirWithPoolTxns, config=tconf,
    #                    ha=nodeHa, cliha=nodeCHa, pluginPaths=allPluginsPath)
    # looper.add(newNode)
    # txnPoolNodeSet[-1] = newNode

    # Delay catchup reply processing so LedgerState does not change
    # delay_catchup_reply = 5
    # newNode.nodeIbStasher.delay(cr_delay(delay_catchup_reply))
    # looper.run(checkNodesConnected(txnPoolNodeSet))
    #
    # # Make sure ledger starts syncing (sufficient consistency proofs received)
    # looper.run(eventually(check_ledger_state, newNode, DOMAIN_LEDGER_ID,
    #                       LedgerState.syncing, retryWait=.5, timeout=5))
    #
    # # Not accurate timeout but a conservative one
    # timeout = waits.expectedPoolGetReadyTimeout(len(txnPoolNodeSet)) + \
    #           2*delay_catchup_reply
    # waitNodeDataEquality(looper, newNode, *txnPoolNodeSet[:4],
    #                      customTimeout=timeout)
    #
    sendReqsToNodesAndVerifySuffReplies(looper, wallet, client, 5)
    waitNodeDataEquality(looper, newNode, *txnPoolNodeSet[:4])


def test_node_load_after_add_then_disconnect(newNodeCaughtUp, txnPoolNodeSet,
                                             tconf,
                                             nodeSetWithNodeAddedAfterSomeTxns,
                                             tdirWithPoolTxns, allPluginsPath,
                                             poolTxnStewardData, capsys):
    """
    A node that restarts after some transactions should eventually get the
    transactions which happened while it was down
    :return:
    """
    looper, newNode, client, wallet, _, _ = nodeSetWithNodeAddedAfterSomeTxns
    with capsys.disabled():
        print("Stopping node {} with pool ledger size {}".
              format(newNode, newNode.poolManager.txnSeqNo))
    disconnect_node_and_ensure_disconnected(looper, txnPoolNodeSet, newNode)
    looper.removeProdable(newNode)

    client_batches = 80
    txns_per_batch = 10
    for i in range(client_batches):
        s = perf_counter()
        sendReqsToNodesAndVerifySuffReplies(looper, wallet, client,
                                            txns_per_batch,
                                            override_timeout_limit=True)
        with capsys.disabled():
            print('{} executed {} client txns in {:.2f} seconds'.
                  format(i+1, txns_per_batch, perf_counter()-s))

    with capsys.disabled():
        print("Starting the stopped node, {}".format(newNode))
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
    waitNodeDataEquality(looper, newNode, *txnPoolNodeSet[:4])


def test_nodestack_contexts_are_discrete(txnPoolNodeSet):
    assert txnPoolNodeSet[0].nodestack.ctx != txnPoolNodeSet[1].nodestack.ctx


def test_node_load_after_disconnect(looper, txnPoolNodeSet, tconf,
                                    tdirWithPoolTxns, allPluginsPath,
                                    poolTxnStewardData, capsys):

    client, wallet = buildPoolClientAndWallet(poolTxnStewardData,
                                              tdirWithPoolTxns,
                                              clientClass=TestClient)
    looper.add(client)
    looper.run(client.ensureConnectedToNodes())

    nodes = txnPoolNodeSet
    x = nodes[-1]

    with capsys.disabled():
        print("Stopping node {} with pool ledger size {}".
              format(x, x.poolManager.txnSeqNo))

    disconnect_node_and_ensure_disconnected(looper, txnPoolNodeSet, x)
    looper.removeProdable(x)

    client_batches = 80
    txns_per_batch = 10
    for i in range(client_batches):
        s = perf_counter()
        sendReqsToNodesAndVerifySuffReplies(looper, wallet, client,
                                            txns_per_batch,
                                            override_timeout_limit=True)
        with capsys.disabled():
            print('{} executed {} client txns in {:.2f} seconds'.
                  format(i+1, txns_per_batch, perf_counter()-s))


def test_node_load_after_one_node_drops_all_msgs(looper, txnPoolNodeSet, tconf,
                                             tdirWithPoolTxns, allPluginsPath,
                                             poolTxnStewardData, capsys):

    client, wallet = buildPoolClientAndWallet(poolTxnStewardData,
                                              tdirWithPoolTxns,
                                              clientClass=TestClient)
    looper.add(client)
    looper.run(client.ensureConnectedToNodes())

    nodes = txnPoolNodeSet
    x = nodes[-1]

    with capsys.disabled():
        print("Patching node {}".format(x))

    def handleOneNodeMsg(self, wrappedMsg):
        # do nothing with an incoming node message
        pass

    x.handleOneNodeMsg = MethodType(handleOneNodeMsg, x)

    client_batches = 120
    txns_per_batch = 25
    for i in range(client_batches):
        s = perf_counter()
        sendReqsToNodesAndVerifySuffReplies(looper, wallet, client,
                                            txns_per_batch,
                                            override_timeout_limit=True)
        with capsys.disabled():
            print('{} executed {} client txns in {:.2f} seconds'.
                  format(i+1, txns_per_batch, perf_counter()-s))
