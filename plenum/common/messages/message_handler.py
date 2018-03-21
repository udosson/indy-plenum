from common.serializers.serialization import transport_serialization
from plenum.common.messages.message import Message, SignedMessage
from plenum.common.messages.message_factory import MessageFactory
from plenum.server.req_authenticator import ReqAuthenticator
from stp_core.common.log import getlogger

logger = getlogger()


class MessageHandler:
    def __init__(self, authenticator: ReqAuthenticator, message_factory: MessageFactory):
        self.authenticator = authenticator
        self.message_factory = message_factory

    # PUBLIC

    def process_input_msg(self, serialized_msg: bytes) -> Message:
        # 1. deserialize to dict
        msg_as_dict = self._deserialize(serialized_msg)

        # 2. dict to Message instance
        msg = self._instantiate_from_dict(msg_as_dict)

        # 3. validate
        msg.validate()

        # 4. verify signature and deserialize payload if signed wrapper
        if isinstance(msg, SignedMessage):
            self.process_signed_msg(msg)

        return msg

    def process_signed_msg(self, msg: SignedMessage):
        # 1. verify signature
        self._verify_signature(msg)

        # 2. deserialize payload
        msg_payload_as_dict = self._deserialize(msg.msg_serialized, msg.serialization)

        # 3. dict to Message instance
        msg_payload = self._instantiate_from_dict(msg_payload_as_dict)

        # 4. validate
        msg_payload.validate()

        # 5. set payload
        msg.msg = msg_payload

    def process_output_msg(self, msg: Message) -> bytes:
        msg.validate()
        return msg.to_dict()

    # PROTECTED

    @staticmethod
    def _deserialize(serialized_msg: bytes, serialization=None) -> dict:
        # TODO: support MsgPack only for now
        return transport_serialization.deserialize(serialized_msg)

    @staticmethod
    def _serialize(msg: Message, serialization=None) -> dict:
        # TODO: support MsgPack only for now
        return transport_serialization.deserialize(serialized_msg)

    def _instantiate_from_dict(self, msg_as_dict: dict) -> Message:
        msg = self.message_factory.get_instance(**msg_as_dict)
        msg.init_from_dict(msg_as_dict)
        return msg

    def _verify_signature(self, msg: SignedMessage):
        identifiers = self.authenticator.authenticate(msg)
        logger.debug("{} authenticated {} signature on msg {}".
                     format(self, identifiers, msg.as_dict()),
                     extra={"cli": True,
                            "tags": ["node-msg-processing"]})
