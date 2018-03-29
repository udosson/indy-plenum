from typing import List

from plenum.common.messages.constants.message_constants import POOL_MULTI_SIG_BLS
from plenum.common.messages.fields import IterableField, SerializedValueField, AnyValueField, NonEmptyStringField, \
    EnumField, NonNegativeNumberField, LedgerIdField, MerkleRootField, TimestampField
from plenum.common.messages.message import Message, MessageData
from plenum.common.messages.message_base import MessageField, MessageBase
from plenum.common.messages.request import RequestMetadata


class LedgerMetadata(MessageBase):
    schema = (
        ('ledgerId', 'ledgerId', LedgerIdField()),
        ('rootHash', 'rootHash', MerkleRootField()),
        ('size', 'size', NonNegativeNumberField()),
    )

    def __init__(self, ledgerId: int = None, rootHash: str = None,
                 size: int = None):
        self.ledgerId = ledgerId
        self.rootHash = rootHash
        self.size = size


class StateMetadata(MessageBase):
    schema = (
        ('timestamp', 'timestamp', TimestampField()),
        ('poolRootHash', 'poolRootHash', MerkleRootField()),
        ('rootHash', 'rootHash', MerkleRootField()),
    )

    def __init__(self, ledgerId: int = None, rootHash: str = None,
                 size: int = None):
        self.ledgerId = ledgerId
        self.rootHash = rootHash
        self.size = size


class SignedState(MessageBase):
    schema = (
        ('ledgerMetadata', 'ledgerMetadata', MessageField(cls=LedgerMetadata)),
        ('stateMetadata', 'stateMetadata', MessageField(cls=StateMetadata)),
    )

    def __init__(self, ledgerMetadata: LedgerMetadata = None,
                 stateMetadata: StateMetadata = None):
        self.ledgerMetadata = ledgerMetadata
        self.stateMetadata = stateMetadata


class PoolMultiSignature(MessageBase):
    schema = (
        ('typename', 'type', EnumField(expected_values=[POOL_MULTI_SIG_BLS])),
        ('frm', 'from', IterableField(NonEmptyStringField())),
        ('value', 'value', SerializedValueField()),
        ('signedState', 'signedState', SerializedValueField()),
    )

    def __init__(self, typename: str = None, frm: List[str] = None,
                 value=None, signedState=None):
        self.typename = typename
        self.frm = frm
        self.value = value
        self.signedState = signedState


class ReplyResult(MessageBase):
    schema = (
        ('result', 'result', AnyValueField()),
        ('multiSignature', 'multiSignature', MessageField(cls=PoolMultiSignature)),
        ('stateProof', 'multiSignature', IterableField(SerializedValueField())),
        ('auditProof', 'multiSignature', IterableField(SerializedValueField())),
    )




class ReplyData(MessageData):
    schema = (
        ('results', 'results', IterableField(MessageField(cls=ReplyResult))),
    )

    def __init__(self, results: List[ReplyResult] = None):
        self.results = results


class Reply(Message[ReplyData, RequestMetadata]):
    typename = "REPLY"
    version = 0
    data_cls = ReplyData
    metadata_cls = RequestMetadata
