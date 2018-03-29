import os

import base58
import pytest

from plenum.common.messages.client_messages import NymRequest, SignedNymRequest, NymRequestData, SignedNodeRequest, \
    NodeRequest, NodeRequestData
from plenum.common.messages.constants.message_constants import MSG_TYPE, MSG_VERSION, SIGNED_MSG_SER, \
    SERIALIZATION_MSG_PACK, SIGNED_MSG_DATA_SERIALIZED, SIGNED_MSG_SIGNATURE, SIGNED_MSG_DATA, REQUEST_ID, REQUEST_FRM, \
    MSG_SIGNATURE_VALUES, MSG_SIGNATURE_TYPE, MSG_SIGNATURE_VALUES_VALUE, MSG_SIGNATURE_VALUES_FROM
from plenum.common.messages.request import RequestMetadata, Request
from plenum.common.messages.signed_message import Signature, SignatureValue

STATE_ROOT = base58.b58encode(os.urandom(32))
TXN_ROOT = base58.b58encode(os.urandom(32))
DID = base58.b58encode(os.urandom(16))
VERKEY = "~" + base58.b58encode(os.urandom(16))
BLSKEY = base58.b58encode(os.urandom(128))


@pytest.fixture(params=['from_dict', 'in_constructor'])
def nym(request):
    if request.param == 'from_dict':
        msg = SignedNymRequest()
        msg.init_from_dict(
            {
                MSG_TYPE: "NYM",
                MSG_VERSION: 0,
                SIGNED_MSG_SER: SERIALIZATION_MSG_PACK,
                SIGNED_MSG_DATA_SERIALIZED: b"55555",
                SIGNED_MSG_SIGNATURE: {
                    MSG_SIGNATURE_TYPE: "ed25519",
                    MSG_SIGNATURE_VALUES: [
                        {
                            MSG_SIGNATURE_VALUES_FROM: "client1",
                            MSG_SIGNATURE_VALUES_VALUE: "signature_value"
                        }
                    ]
                },
                SIGNED_MSG_DATA: {
                    "from": "client1",
                    "protocolVersion": 2,
                    "data": {
                        "alias": "nym_alias",
                        "verkey": VERKEY,
                        "did": DID,
                        "role": "0"
                    },
                    "metadata": {
                        REQUEST_FRM: "client1",
                        REQUEST_ID: 202
                    }
                }
            }
        )
    else:
        nym_req = NymRequest(frm="client1",
                             protocol_version=2,
                             data=NymRequestData(
                                 alias="nym_alias",
                                 verkey=VERKEY,
                                 did=DID,
                                 role="0"
                             ),
                             metadata=RequestMetadata(
                                 frm="client1",
                                 reqId=202
                             ))
        signature = Signature(typename="ed25519",
                              values=[SignatureValue(
                                  frm="client1", value="signature_value")])
        msg = SignedNymRequest(serialization=SERIALIZATION_MSG_PACK,
                               msg_serialized=b"55555",
                               msg=nym_req,
                               signature=signature)
    return msg


@pytest.fixture(params=['from_dict', 'in_constructor'])
def node(request):
    if request.param == 'from_dict':
        msg = SignedNodeRequest()
        msg.init_from_dict(
            {
                MSG_TYPE: "NODE",
                MSG_VERSION: 0,
                SIGNED_MSG_SER: SERIALIZATION_MSG_PACK,
                SIGNED_MSG_DATA_SERIALIZED: b"55555",
                SIGNED_MSG_SIGNATURE: {
                    MSG_SIGNATURE_TYPE: "ed25519",
                    MSG_SIGNATURE_VALUES: [
                        {
                            MSG_SIGNATURE_VALUES_FROM: "client1",
                            MSG_SIGNATURE_VALUES_VALUE: "signature_value"
                        }
                    ]
                },
                SIGNED_MSG_DATA: {
                    "from": "client1",
                    "protocolVersion": 2,
                    "data": {
                        "alias": "node_alias",
                        "verkey": VERKEY,
                        "did": DID,
                        "nodeIp": "192.168.1.1",
                        "nodePort": 9701,
                        "clientIp": "192.168.1.2",
                        "clientPort": 9702,
                        "services": ["VALIDATOR"],
                        "blskey": BLSKEY
                    },
                    "metadata": {
                        REQUEST_FRM: "client1",
                        REQUEST_ID: 202
                    }
                }
            }
        )
    else:
        nym_req = NodeRequest(frm="client1",
                              protocol_version=2,
                              data=NodeRequestData(
                                  alias="node_alias",
                                  verkey=VERKEY,
                                  did=DID,
                                  node_ip="192.168.1.1",
                                  node_port=9701,
                                  client_ip="192.168.1.2",
                                  client_port=9702,
                                  services=["VALIDATOR"],
                                  blskey=BLSKEY
                              ),
                              metadata=RequestMetadata(
                                  frm="client1",
                                  reqId=202
                              ))
        signature = Signature(typename="ed25519",
                              values=[SignatureValue(
                                  frm="client1", value="signature_value")])
        msg = SignedNodeRequest(serialization=SERIALIZATION_MSG_PACK,
                                msg_serialized=b"55555",
                                msg=nym_req,
                                signature=signature)
    return msg


def validate_signature(msg):
    assert msg.serialization == "MsgPack"
    assert msg.msg_serialized == b"55555"

    signature = msg.signature
    assert isinstance(signature, Signature)
    assert signature.typename == "ed25519"
    assert signature.threshold is None
    signature_value = signature.values[0]
    assert signature_value.frm == "client1"
    assert signature_value.value == "signature_value"


def validate_req_metadata(req: Request):
    metadata = req.metadata
    assert isinstance(metadata, RequestMetadata)
    assert metadata.frm == "client1"
    assert metadata.reqId == 202


def test_nym(nym):
    signed_msg = nym  # type: SignedNymRequest

    signed_msg.validate()

    assert signed_msg.typename == "1"
    assert signed_msg.version == 0
    validate_signature(signed_msg)

    req = signed_msg.msg
    assert isinstance(req, NymRequest)
    assert req.typename == "1"
    assert req.version == 0
    assert req.protocol_version == 2
    assert req.frm == "client1"

    validate_req_metadata(req)

    assert isinstance(req.data, NymRequestData)
    assert req.data.alias == "nym_alias"
    assert req.data.verkey == VERKEY
    assert req.data.did == DID
    assert req.data.role == "0"


def test_node(node):
    signed_msg = node  # type: SignedNodeRequest

    signed_msg.validate()

    assert signed_msg.typename == "0"
    assert signed_msg.version == 0
    validate_signature(signed_msg)

    req = signed_msg.msg
    assert isinstance(req, NodeRequest)
    assert req.typename == "0"
    assert req.version == 0
    assert req.protocol_version == 2
    assert req.frm == "client1"

    validate_req_metadata(req)

    assert isinstance(req.data, NodeRequestData)
    assert req.data.alias == "node_alias"
    assert req.data.verkey == VERKEY
    assert req.data.did == DID
    assert req.data.node_ip == "192.168.1.1"
    assert req.data.node_port == 9701
    assert req.data.client_ip == "192.168.1.2"
    assert req.data.client_port == 9702
    assert req.data.services == ["VALIDATOR"]
    assert req.data.blskey == BLSKEY
