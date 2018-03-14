from common.serializers.serialization import transport_serialization
from plenum.common.messages.message import Message
from plenum.common.messages.message_base import MessageValidator
from plenum.common.messages.message_factory import MessageFactory
from plenum.server.req_authenticator import ReqAuthenticator
from stp_core.common.log import getlogger

logger = getlogger()

class MessageHandler:

    def __init__(self, authenticator: ReqAuthenticator, message_factory: MessageFactory):
        self.authenticator = authenticator
        self.message_factory = message_factory
        self.message_validator = MessageValidator()


    # PUBLIC

    def process_input_msg(self, serialized_msg: bytes) -> Message:
        msg_as_dict = self._deserialize_outer(serialized_msg)
        msg = self._instantiate_from_dict(msg_as_dict)

        self._validate_outer(msg)
        self._verify_signature(msg)

        self._deserialize_inner(msg)
        self._validate_inner(msg)

        return msg


    def process_output_msg(self, msg: Message) -> bytes:
        pass

    # PROTECTED

    def _deserialize_outer(self, serialized_msg: bytes) -> dict:
        return transport_serialization.deserialize(serialized_msg)

    def _instantiate_from_dict(self, msg_as_dict: dict) -> Message:
        msg = self.message_factory.get_instance(**msg_as_dict)
        msg.init(msg.schemaOuter, **msg_as_dict)
        return msg

    def _validate_outer(self, msg: Message):
        self.message_validator.validate(msg.schemaOuter, msg.as_dict())

    def _verify_signature(self, msg: Message):
        """
        :return: None; raises an exception if the signature is not valid
        """
        signature = msg.signature
        if not signature:
            return

        # TODO: fix processing of signature types

        values = signature["values"]


        identifiers = self.authenticator.authenticate(msg)
        logger.debug("{} authenticated {} signature on msg {}".
                     format(self, identifiers, msg.as_dict()),
                     extra={"cli": True,
                            "tags": ["node-msg-processing"]})

    def _deserialize_inner(self, msg: Message):
        pass

    def _validate_inner(self, msg: Message):
        pass
