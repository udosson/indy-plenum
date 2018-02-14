from plenum.common.messages.message_factory import MessageFactory


class NodeMessageFactory(MessageFactory):
    def __init__(self):
        super().__init__('plenum.common.messages.node_messages')


node_message_factory = NodeMessageFactory()
