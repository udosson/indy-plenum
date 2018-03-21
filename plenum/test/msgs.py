from plenum.common.messages.fields import NonEmptyStringField
from plenum.common.messages.message import Message, MessageData, MessageMetadata
from plenum.common.messages.message_factory import node_message_factory
from plenum.common.util import randomString


def randomMsg():
    return TestMsg('subject ' + randomString(),
                   'content ' + randomString())


class TestMsgData(MessageData):
    typename = "TESTMSG"
    schema = (
        ("subject", "subject", NonEmptyStringField()),
        ("content", "content", NonEmptyStringField()),
    )

    def __init__(self, subject=None, content=None):
        self.subject = subject
        self.content = content


class TestMsg(Message[TestMsgData, MessageMetadata]):
    typename = "TESTMSG"
    version = 0
    dataCls = TestMsgData


node_message_factory.set_message_class(TestMsg)
