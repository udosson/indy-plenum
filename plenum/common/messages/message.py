from abc import ABCMeta
from typing import Generic, TypeVar

from plenum.common.messages.constants.message_constants import MSG_FROM, MSG_PROTOCOL_VERSION, MSG_DATA, MSG_METADATA, \
    MSG_PLUGIN_DATA
from plenum.common.messages.fields import NonEmptyStringField, NonNegativeNumberField, AnyMapField
from plenum.common.messages.message_base import MessageBase, MessageField


class MessageMetadata(MessageBase):
    pass


class MessageData(MessageBase, metaclass=ABCMeta):
    pass


D = TypeVar('D')
MD = TypeVar('MD')


class Message(MessageBase, Generic[D, MD]):
    typename = None
    version = 0
    data_cls = MessageData
    metadata_cls = MessageMetadata
    need_signature = False

    def __init__(self, protocol_version: int = None, frm: str = None, data: D = None, metadata: MD = None,
                 plugin_data=None):
        self.schema = (
            ("frm", MSG_FROM, NonEmptyStringField()),
            ("protocol_version", MSG_PROTOCOL_VERSION, NonNegativeNumberField(optional=True)),
            ("data", MSG_DATA, MessageField(cls=self.data_cls)),
            ("metadata", MSG_METADATA, MessageField(cls=self.metadata_cls, optional=True)),
            ("plugin_data", MSG_PLUGIN_DATA, AnyMapField(optional=True))
        )

        self.frm = frm
        self.protocol_version = protocol_version
        self.data = data
        self.metadata = metadata
        self.plugin_data = plugin_data
