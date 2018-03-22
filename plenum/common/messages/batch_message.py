from typing import List

from plenum.common.messages.constants.base_message_constants import BATCH, BATCH_MSGS
from plenum.common.messages.fields import IterableField
from plenum.common.messages.message import Message
from plenum.common.messages.message_base import MessageBase, MessageField


class Batch(MessageBase):
    typename = BATCH
    version = 0

    schema = (
        (BATCH_MSGS, IterableField(MessageField(cls=Message))),
    )

    def __init__(self, messages: List[Message] = None):
        self.messages = messages
