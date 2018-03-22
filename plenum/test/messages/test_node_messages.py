import os

import base58
import pytest

from plenum.common.messages.constants.message_constants import MSG_FROM, MSG_PROTOCOL_VERSION, MSG_DATA
from plenum.common.messages.node_messages import Ordered, OrderedData

STATE_ROOT = base58.b58encode(os.urandom(32))
TXN_ROOT = base58.b58encode(os.urandom(32))
DID = base58.b58encode(os.urandom(16))


@pytest.fixture(params=['from_dict', 'in_constructor'])
def ordered(request):
    if request.param == 'from_dict':
        msg = Ordered()
        msg.init_from_dict(
            {
                MSG_FROM: "Node1",
                MSG_PROTOCOL_VERSION: 2,
                MSG_DATA: {
                    "instId": 0,
                    "viewNo": 2,
                    "reqIdr": [(DID, 2), (DID, 100)],
                    "ppSeqNo": 100,
                    "ppTime": 149990690200,
                    "ledgerId": 1,
                    "stateRootHash": STATE_ROOT,
                    "txnRootHash": TXN_ROOT,
                }
            }
        )
    else:
        msg = Ordered(frm="Node1",
                      protocol_version=2,
                      data=OrderedData(
                          instId=0,
                          viewNo=2,
                          reqIdr=[(DID, 2), (DID, 100)],
                          ppSeqNo=100,
                          ppTime=149990690200,
                          ledgerId=1,
                          stateRootHash=STATE_ROOT,
                          txnRootHash=TXN_ROOT
                      ))
    return msg


def test_ordered_msg(ordered):
    msg = ordered # type: Ordered

    msg.validate()

    assert msg.typename == "ORDERED"
    assert msg.version == 0
    assert isinstance(msg.data, OrderedData)
    assert msg.data.instId == 0
    assert msg.data.viewNo == 2
    assert msg.data.reqIdr == [(DID, 2), (DID, 100)]
    assert msg.data.ppSeqNo == 100
    assert msg.data.ppTime == 149990690200
    assert msg.data.ledgerId == 1
    assert msg.data.stateRootHash == STATE_ROOT
    assert msg.data.txnRootHash == TXN_ROOT
