from abc import ABCMeta

from plenum.common.constants import MSG_DATA, MSG_SER, MSG_FROM, MSG_TYPE, MSG_SIGNATURE, MSG_VERSION, \
    MSG_PAYLOAD_PROTOCOL_VERSION, MSG_PAYLOAD_DATA, MSG_PAYLOAD_METADATA, MSG_PAYLOAD_PLUGIN_DATA, MSG_SIGNATURE_TYPE, \
    SIGNATURE_ED25519, SIGNATURE_ED25519_MULTI, MSG_SIGNATURE_VALUES, MSG_SIGNATURE_THRESHOLD, \
    MSG_SIGNATURE_VALUES_FROM, MSG_SIGNATURE_VALUES_VALUE, SERIALIZATION_MSG_PACK
from plenum.common.messages.fields import NonEmptyStringField, NonNegativeNumberField, SerializedValueField, \
    AnyMapField, ComplexField, EnumField, IterableField, LimitedLengthStringField
from plenum.common.messages.message_base import MessageBase
from plenum.config import SIGNATURE_FIELD_LIMIT


class SignatureValue(MessageBase):
    def schema(self):
        return (
            (MSG_SIGNATURE_VALUES_FROM, NonEmptyStringField()),
            (MSG_SIGNATURE_VALUES_VALUE, LimitedLengthStringField(max_length=SIGNATURE_FIELD_LIMIT))
        )


class Message(MessageBase, metaclass=ABCMeta):
    typename = None
    version = 0
    msg = None

    # Schemas
    schema_data = ()
    schema_metadata = ()

    schema_payload = (
        (MSG_PAYLOAD_PROTOCOL_VERSION, NonNegativeNumberField()),
        (MSG_PAYLOAD_DATA, ComplexField(schema=schema_data)),
        (MSG_PAYLOAD_METADATA, ComplexField(schema=schema_metadata)),
        (MSG_PAYLOAD_PLUGIN_DATA, AnyMapField(optional=True)),
    )

    schema_signature_value = (
        (MSG_SIGNATURE_VALUES_FROM, NonEmptyStringField()),
        (MSG_SIGNATURE_VALUES_VALUE, LimitedLengthStringField(max_length=SIGNATURE_FIELD_LIMIT))
    )

    schema_signature = (
        (MSG_SIGNATURE_TYPE,
         EnumField(expected_values=[SIGNATURE_ED25519, SIGNATURE_ED25519_MULTI])),
        (MSG_SIGNATURE_VALUES,
         IterableField(ComplexField(schema=schema_signature_value))),
        (MSG_SIGNATURE_THRESHOLD, NonNegativeNumberField(optional=True)),
    )

    schema_outer = (
        (MSG_TYPE, NonEmptyStringField()),
        (MSG_VERSION, NonNegativeNumberField(optional=True)),  # assume version=0 by default
        (MSG_FROM, NonEmptyStringField()),
        (MSG_SER, EnumField(expected_values=[SERIALIZATION_MSG_PACK], optional=True)),  # assume MsgPack by default
        (MSG_DATA, SerializedValueField()),
        (MSG_SIGNATURE, ComplexField(schema_signature, optional=True)),
    )
