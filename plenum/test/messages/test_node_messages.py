from plenum.common.messages.constants.base_message_constants import MSG_FROM, MSG_PROTOCOL_VERSION, MSG_DATA
from plenum.common.messages.node_messages import Nomination, NominationData, Ordered, OrderedData
from plenum.test.input_validation.utils import b58_by_len


def test_nomination_msg_constr():
    msg = Nomination(frm="Node1",
                     protocol_version=2,
                     data=NominationData(
                         name="name1",
                         instId=1,
                         viewNo=2,
                         ordSeqNo=3
                     ))
    msg.validate()
    assert msg.data.name == "name1"
    assert msg.data.instId == 1
    assert msg.data.viewNo == 2
    assert msg.data.ordSeqNo == 3


def test_nomination_msg_from_dict():
    msg = Nomination()
    msg.init_from_dict(
        {
            MSG_FROM: "Node1",
            MSG_PROTOCOL_VERSION: 2,
            MSG_DATA: {
                "name": "name1",
                "instId": 1,
                "viewNo": 2,
                "ordSeqNo": 3
            }
        }
    )
    msg.validate()
    assert msg.data.name == "name1"
    assert msg.data.instId == 1
    assert msg.data.viewNo == 2
    assert msg.data.ordSeqNo == 3


def test_ordered_msg_constr():
    msg = Ordered(frm="Node1",
                  protocol_version=2,
                  data=OrderedData(
                      instId=0,
                      viewNo=2,
                      reqIdr=[b58_by_len(16), 2],
                      ppSeqNo=100,
                      ppTime=149990690200,
                      ledgerId=1,
                      stateRootHash=b58_by_len(32),
                      txnRootHash=b58_by_len(32)
                  ))
    msg.validate()
    assert msg.data.name == "name1"
    assert msg.data.instId == 1
    assert msg.data.viewNo == 2
    assert msg.data.ordSeqNo == 3


def test_ordered_msg_from_dict():
    msg = Ordered()
    msg.init_from_dict(
        {
            MSG_FROM: "Node1",
            MSG_PROTOCOL_VERSION: 2,
            MSG_DATA: {
                "name": "name1",
                "instId": 1,
                "viewNo": 2,
                "ordSeqNo": 3
            }
        }
    )
    msg.validate()
    assert msg.data.name == "name1"
    assert msg.data.instId == 1
    assert msg.data.viewNo == 2
    assert msg.data.ordSeqNo == 3
