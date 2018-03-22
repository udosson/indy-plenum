import pytest

from plenum.common.messages.constants.base_message_constants import MSG_FROM, MSG_PROTOCOL_VERSION, \
    SERIALIZATION_MSG_PACK, SIGNED_MSG_DATA, SIGNED_MSG_SIGNATURE, SIGNED_MSG_DATA_SERIALIZED, SIGNED_MSG_SER, \
    MSG_VERSION, MSG_TYPE, MSG_METADATA, MSG_DATA
from plenum.common.messages.fields import NonEmptyStringField, LimitedLengthStringField, NonNegativeNumberField
from plenum.common.messages.message import MessageMetadata, MessageData, Message
from plenum.common.messages.signed_message import SignedMessage, Signature, SignatureValue


class TestMessageData(MessageData):
    schema = (
        ("a", "aaa", NonNegativeNumberField()),
        ("b", "bbb", LimitedLengthStringField(max_length=10)),
        ("c", "ccc", NonNegativeNumberField(optional=True))
    )

    def __init__(self, a: int = None, b: str = None, c: int = None):
        self.a = a
        self.b = b
        self.c = c


class TestMessageMetadata(MessageMetadata):
    schema = (
        ("f1", "f111", NonNegativeNumberField()),
        ("f2", "f222", NonEmptyStringField()),
    )

    def __init__(self, f1: int = None, f2: str = None):
        self.f1 = f1
        self.f2 = f2


class TestMessage(Message[TestMessageData, TestMessageMetadata]):
    typename = "TEST_MESSAGE"
    version = 1
    dataCls = TestMessageData
    metadataCls = TestMessageMetadata


class TestSignedMessage(SignedMessage[TestMessage]):
    typename = "SIGNED_TEST_MESSAGE"
    version = 2
    msgCls = TestMessage


@pytest.fixture(params=['from_dict', 'in_constructor'])
def msg_inited(request):
    if request.param == 'from_dict':
        msg = TestMessage()
        msg.init_from_dict(
            {
                MSG_FROM: "client1",
                MSG_PROTOCOL_VERSION: 2,
                MSG_DATA: {
                    "aaa": 0,
                    "bbb": "1",
                },
                MSG_METADATA: {
                    "f111": 1,
                    "f222": "2"
                }
            }
        )
    else:
        data = TestMessageData(a=0, b="1")
        metadata = TestMessageMetadata(f1=1, f2="2")
        msg = TestMessage(protocol_version=2,
                          frm="client1",
                          data=data,
                          metadata=metadata)
    return msg


@pytest.fixture(params=['from_dict', 'in_constructor'])
def signed_msg_inited(request):
    if request.param == 'from_dict':
        msg = TestSignedMessage()
        msg.init_from_dict(
            {
                MSG_TYPE: "SIGNED_TEST_MESSAGE",
                MSG_VERSION: 2,
                SIGNED_MSG_SER: SERIALIZATION_MSG_PACK,
                SIGNED_MSG_DATA_SERIALIZED: b"55555",
                SIGNED_MSG_SIGNATURE: {
                    "type": "ed25519",
                    "values": [
                        {
                            "from": "client1",
                            "value": "signature_value"
                        }
                    ]
                },
                SIGNED_MSG_DATA: {
                    "from": "client1",
                    "protocolVersion": 2,
                    "data": {
                        "aaa": 0,
                        "bbb": "1",
                    },
                    "metadata": {
                        "f111": 1,
                        "f222": "2"
                    }
                }
            }
        )
    else:
        data = TestMessageData(a=0, b="1")
        metadata = TestMessageMetadata(f1=1, f2="2")
        msg = TestMessage(protocol_version=2,
                          frm="client1",
                          data=data,
                          metadata=metadata)
        signature = Signature(type="ed25519",
                              values=[SignatureValue(
                                  frm="client1", value="signature_value")])
        msg = TestSignedMessage(serialization=SERIALIZATION_MSG_PACK,
                                msg_serialized=b"55555",
                                signature=signature,
                                msg=msg)
    return msg


def test_instantiate_msg():
    assert TestMessage()
    assert TestSignedMessage()


def test_init_msg(msg_inited):
    msg = msg_inited  # type: TestMessage

    assert msg.typename == "TEST_MESSAGE"
    assert msg.version == 1
    assert msg.protocol_version == 2
    assert msg.frm == "client1"

    assert isinstance(msg.data, TestMessageData)
    assert msg.data.a == 0
    assert msg.data.b == "1"
    assert msg.data.c is None

    assert isinstance(msg.metadata, TestMessageMetadata)
    assert msg.metadata.f1 == 1
    assert msg.metadata.f2 == "2"

    assert msg.plugin_data is None


def test_init_signed_msg(signed_msg_inited):
    signed_msg = signed_msg_inited  # type: TestSignedMessage

    assert signed_msg.typename == "SIGNED_TEST_MESSAGE"
    assert signed_msg.version == 2
    assert signed_msg.serialization == SERIALIZATION_MSG_PACK
    assert signed_msg.msg_serialized == b"55555"

    signature = signed_msg.signature
    assert isinstance(signature, Signature)
    assert signature.threshold is None
    signature_value = signature.values[0]
    assert signature_value.frm == "client1"
    assert signature_value.value == "signature_value"

    msg = signed_msg.msg
    assert isinstance(msg, TestMessage)
    assert msg.typename == "TEST_MESSAGE"
    assert msg.version == 1
    assert msg.protocol_version == 2
    assert msg.frm == "client1"

    assert isinstance(msg.data, TestMessageData)
    assert msg.data.a == 0
    assert msg.data.b == "1"
    assert msg.data.c is None

    assert isinstance(msg.metadata, TestMessageMetadata)
    assert msg.metadata.f1 == 1
    assert msg.metadata.f2 == "2"

    assert msg.plugin_data is None


def test_validate_msg(msg_inited):
    msg = msg_inited  # type: TestMessage
    msg.validate()

    msg.protocol_version = b'ffff'
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('expected types')

    msg.protocol_version = 0
    msg.data.a = -5
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('negative value')

    msg.data.a = 5
    msg.metadata.f2 = 1111
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('expected types')


def test_validate_signed_msg(signed_msg_inited):
    msg = signed_msg_inited  # type: TestSignedMessage
    msg.validate()

    msg.serialization = "aaaaa"
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('has to be one of')

    msg.serialization = None
    msg.msg.data.a = -5
    with pytest.raises(TypeError) as ex_info:
        msg.validate()
    assert ex_info.match('negative value')
