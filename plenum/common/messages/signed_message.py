from typing import List, Generic, TypeVar

from plenum.common.messages.constants.message_constants import MSG_SIGNATURE_VALUES_FROM, MSG_SIGNATURE_VALUES_VALUE, \
    MSG_SIGNATURE_TYPE, SIGNATURE_ED25519, MSG_SIGNATURE_VALUES, SIGNATURE_ED25519_MULTI, MSG_SIGNATURE_THRESHOLD, \
    SIGNED_MSG_SER, SIGNED_MSG_DATA_SERIALIZED, SIGNED_MSG_SIGNATURE, SIGNED_MSG_DATA, SERIALIZATION_MSG_PACK
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
        ("typename", MSG_SIGNATURE_TYPE,
         EnumField(expected_values=[SIGNATURE_ED25519, SIGNATURE_ED25519_MULTI])),
        ("values", MSG_SIGNATURE_VALUES,
         IterableField(MessageField(cls=SignatureValue))),
        ("threshold", MSG_SIGNATURE_THRESHOLD, NonNegativeNumberField(optional=True))
    )

    def __init__(self, typename: str = None, values: List[SignatureValue] = None, threshold: int = None):
        self.typename = typename
        self.values = values
        self.threshold = threshold


M = TypeVar('M')


class SignedMessage(MessageBase, Generic[M]):
    typename = None
    version = 0

    msg_cls = Message

    def __init__(self, serialization: str = None, msg_serialized: bytes = None, msg: M = None,
                 signature: Signature = None):
        self.schema = (
            # assume MsgPack by default
            ("serialization", SIGNED_MSG_SER, EnumField(expected_values=[SERIALIZATION_MSG_PACK], optional=True)),
            ("msg_serialized", SIGNED_MSG_DATA_SERIALIZED, SerializedValueField()),
            ("signature", SIGNED_MSG_SIGNATURE, MessageField(cls=Signature)),
            ("msg", SIGNED_MSG_DATA, MessageField(cls=self.msg_cls, optional=True)),
        )

        self.serialization = serialization
        self.msg_serialized = msg_serialized
        self.msg = msg
        self.signature = signature
