from typing import List, Generic, TypeVar

from plenum.common.messages.constants.base_message_constants import SIGNED_MSG_SER, MSG_SIGNATURE_TYPE, \
    SIGNATURE_ED25519, SIGNATURE_ED25519_MULTI, MSG_SIGNATURE_VALUES, MSG_SIGNATURE_VALUES_FROM, SERIALIZATION_MSG_PACK, \
    MSG_SIGNATURE_THRESHOLD, SIGNED_MSG_SIGNATURE, SIGNED_MSG_DATA, SIGNED_MSG_DATA_SERIALIZED, \
    MSG_SIGNATURE_VALUES_VALUE
from plenum.common.messages.fields import NonEmptyStringField, NonNegativeNumberField, EnumField, IterableField, \
    LimitedLengthStringField, SerializedValueField
from plenum.common.messages.message import Message
from plenum.common.messages.message_base import MessageBase, MessageField
from plenum.config import SIGNATURE_FIELD_LIMIT


class SignatureValue(MessageBase):
    schema = (
        ("frm", MSG_SIGNATURE_VALUES_FROM, NonEmptyStringField()),
        ("value", MSG_SIGNATURE_VALUES_VALUE, LimitedLengthStringField(max_length=SIGNATURE_FIELD_LIMIT))
    )

    def __init__(self, frm: str = None, value: str = None):
        self.frm = frm
        self.value = value


class Signature(MessageBase):
    schema = (
        ("type", MSG_SIGNATURE_TYPE,
         EnumField(expected_values=[SIGNATURE_ED25519, SIGNATURE_ED25519_MULTI])),
        ("values", MSG_SIGNATURE_VALUES,
         IterableField(MessageField(cls=SignatureValue))),
        ("threshold", MSG_SIGNATURE_THRESHOLD, NonNegativeNumberField(optional=True))
    )

    def __init__(self, type: str = None, values: List[SignatureValue] = None, threshold: int = None):
        self.type = type
        self.values = values
        self.threshold = threshold


M = TypeVar('M')


class SignedMessage(MessageBase, Generic[M]):
    typename = None
    version = 0

    msgCls = Message

    def __init__(self, serialization: str = None, msg_serialized: bytes = None, msg: M = None,
                 signature: Signature = None):
        self.schema = (
            # assume MsgPack by default
            ("serialization", SIGNED_MSG_SER, EnumField(expected_values=[SERIALIZATION_MSG_PACK], optional=True)),
            ("msg_serialized", SIGNED_MSG_DATA_SERIALIZED, SerializedValueField()),
            ("signature", SIGNED_MSG_SIGNATURE, MessageField(cls=Signature)),
            ("msg", SIGNED_MSG_DATA, MessageField(cls=self.msgCls, optional=True)),
        )

        self.serialization = serialization
        self.msg_serialized = msg_serialized
        self.msg = msg
        self.signature = signature
