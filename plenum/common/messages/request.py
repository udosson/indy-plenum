from hashlib import sha256

from common.serializers.serialization import req_digest_serialization
from plenum.common.messages.constants.message_constants import REQUEST_ID, REQUEST_FRM
from plenum.common.messages.fields import NonEmptyStringField, NonNegativeNumberField
from plenum.common.messages.message import MessageMetadata, Message, D
from plenum.common.messages.signed_message import SignedMessage
from plenum.common.tools import lazy_field


class RequestMetadata(MessageMetadata):
    schema = (
        ("frm", REQUEST_FRM, NonEmptyStringField()),
        ("reqId", REQUEST_ID, NonNegativeNumberField()),
    )

    def __init__(self, frm: str = None, reqId: int = None) -> None:
        self.frm = frm
        self.reqId = reqId


class Request(Message[D, RequestMetadata]):
    metadata_cls = RequestMetadata

    @lazy_field
    def getDigest(self):
        return sha256(req_digest_serialization.serialize(self.to_dict())).hexdigest()


class ReadRequest(Request[D]):
    pass


class WriteRequest(SignedMessage[Request[D]]):
    pass
