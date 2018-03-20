from abc import ABCMeta

from indy_common.types import SchemaField
from plenum.common.constants import MSG_SER, MSG_FROM, MSG_TYPE, MSG_VERSION, \
    MSG_PAYLOAD_PROTOCOL_VERSION, MSG_PAYLOAD_DATA, MSG_PAYLOAD_METADATA, MSG_PAYLOAD_PLUGIN_DATA, MSG_SIGNATURE_TYPE, \
    SIGNATURE_ED25519, SIGNATURE_ED25519_MULTI, MSG_SIGNATURE_VALUES, MSG_SIGNATURE_VALUES_FROM, SERIALIZATION_MSG_PACK, \
    MSG_SIGNATURE_THRESHOLD
from plenum.common.messages.fields import NonEmptyStringField, NonNegativeNumberField, AnyMapField, \
    EnumField, IterableField, LimitedLengthStringField, MessageField
from plenum.common.messages.message_base import MessageBase, InputField
from plenum.config import SIGNATURE_FIELD_LIMIT


class SignatureValue(MessageBase):
    def __init__(self):
        self.frm = InputField(MSG_SIGNATURE_VALUES_FROM, NonEmptyStringField())
        self.value = InputField(MSG_SIGNATURE_VALUES_FROM, LimitedLengthStringField(max_length=SIGNATURE_FIELD_LIMIT))


class Signature(MessageBase):
    def __init__(self):
        self.type = InputField(MSG_SIGNATURE_TYPE,
                               EnumField(expected_values=[SIGNATURE_ED25519, SIGNATURE_ED25519_MULTI]))
        self.values = InputField(MSG_SIGNATURE_VALUES,
                                 IterableField(MessageField(cls=SignatureValue)))
        self.threshold = InputField(MSG_SIGNATURE_THRESHOLD,
                                    NonNegativeNumberField(optional=True))


class MessageMetadata(MessageBase):
    pass


class MessagePayloadData(MessageBase, metaclass=ABCMeta):
    pass


class Message(MessageBase, metaclass=ABCMeta):
    MessageDataClass = None
    MessageMetadataClass = MessageMetadata

    class MessagePayload(MessageBase):
        def __init__(self):
            self.protocol_version = InputField(MSG_PAYLOAD_PROTOCOL_VERSION,
                                               NonNegativeNumberField())
            self.data = InputField(MSG_PAYLOAD_DATA,
                                          MessageField(cls=Message.MessageDataClass))
            self.metadata = InputField(MSG_PAYLOAD_METADATA,
                                              MessageField(cls=Message.MessageMetadataClass))
            self.plugin_data = InputField(MSG_PAYLOAD_PLUGIN_DATA,
                                                 AnyMapField())

    def __init__(self):
        self.typename = InputField(MSG_TYPE,
                                   NonEmptyStringField())
        # assume version=0 by default
        self.version = InputField(MSG_VERSION,
                                  NonNegativeNumberField(optional=True))
        self.frm = InputField(MSG_FROM,
                              NonEmptyStringField())
        # assume no serialization by default
        self.serialization = InputField(MSG_SER,
                                        EnumField(expected_values=[SERIALIZATION_MSG_PACK], optional=True))
        self.msg_serialized = InputField(MSG_FROM,
                                         NonEmptyStringField())
        self.msg = InputField(MSG_FROM,
                                     NonEmptyStringField())
        self.signature = InputField(MSG_FROM,
                                           NonEmptyStringField())
