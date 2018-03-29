from typing import TypeVar, NamedTuple

from plenum.common.constants import BATCH, BLACKLIST, REQACK, REQNACK, REJECT, \
    POOL_LEDGER_TXNS, ORDERED, PROPAGATE, PREPREPARE, PREPARE, COMMIT, CHECKPOINT, THREE_PC_STATE, CHECKPOINT_STATE, \
    REPLY, INSTANCE_CHANGE, LEDGER_STATUS, CONSISTENCY_PROOF, CATCHUP_REQ, CATCHUP_REP, VIEW_CHANGE_DONE, CURRENT_STATE, \
    MESSAGE_REQUEST, MESSAGE_RESPONSE, OBSERVED_DATA, BATCH_COMMITTED
from plenum.common.messages.fields import NonNegativeNumberField, IterableField, \
    AnyValueField, RequestIdentifierField, TimestampField, \
    LedgerIdField, MerkleRootField, Base58Field, LedgerInfoField, AnyField, ChooseField, AnyMapField, \
    LimitedLengthStringField, BlsMultiSignatureField
from plenum.common.messages.message import Message, MessageData, MessageMetadata, D
from plenum.common.messages.message_base import \
    MessageBase, MessageField
from plenum.common.request import Request
from plenum.common.types import f
from plenum.config import NAME_FIELD_LIMIT, DIGEST_FIELD_LIMIT, SENDER_CLIENT_FIELD_LIMIT, HASH_FIELD_LIMIT, \
    BLS_SIG_LIMIT


# BASE NODE MSG

class NodeMessage(Message[D, MessageMetadata]):
    pass


# TODO implement actual rules
class BlacklistMsg(MessageBase):
    typename = BLACKLIST
    schema = (
        (f.SUSP_CODE.nm, AnyValueField()),
        (f.NODE_NAME.nm, AnyValueField()),
    )


# TODO implement actual rules
class RequestAck(MessageBase):
    typename = REQACK
    schema = (
        (f.IDENTIFIER.nm, AnyValueField()),
        (f.REQ_ID.nm, AnyValueField())
    )


# TODO implement actual rules
class RequestNack(MessageBase):
    typename = REQNACK
    schema = (
        (f.IDENTIFIER.nm, AnyValueField()),
        (f.REQ_ID.nm, AnyValueField()),
        (f.REASON.nm, AnyValueField()),
    )


# TODO implement actual rules
class Reject(MessageBase):
    typename = REJECT
    schema = (
        (f.IDENTIFIER.nm, AnyValueField()),
        (f.REQ_ID.nm, AnyValueField()),
        (f.REASON.nm, AnyValueField()),
    )


# TODO implement actual rules
class PoolLedgerTxns(MessageBase):
    typename = POOL_LEDGER_TXNS
    schema = (
        (f.TXN.nm, AnyValueField()),
    )


# ORDERED

class OrderedData(MessageData):
    schema = (
        ('instId', 'instId', NonNegativeNumberField()),
        ('viewNo', 'viewNo', NonNegativeNumberField()),
        ('reqIdr', 'reqIdr', IterableField(RequestIdentifierField())),
        ('ppSeqNo', 'ppSeqNo', NonNegativeNumberField()),
        ('ppTime', 'ppTime', TimestampField()),
        ('ledgerId', 'ledgerId', LedgerIdField()),
        ('stateRootHash', 'stateRootHash', MerkleRootField(nullable=True)),
        ('txnRootHash', 'txnRootHash', MerkleRootField(nullable=True)),
    )

    def __init__(self, instId: int = None, viewNo: int = None,
                 reqIdr=None, ppSeqNo: int=None, ppTime: int=None, ledgerId: int=None,
                 stateRootHash: str = None, txnRootHash: str = None):
        self.instId = instId
        self.viewNo = viewNo
        self.reqIdr = reqIdr
        self.ppSeqNo = ppSeqNo
        self.ppTime = ppTime
        self.ledgerId = ledgerId
        self.stateRootHash = stateRootHash
        self.txnRootHash = txnRootHash


class Ordered(NodeMessage[OrderedData]):
    typename = "ORDERED"
    version = 0
    data_cls = OrderedData

# PROPAGATE

class PropagateData(MessageBase):
    schema = (
        ('request', 'request', AnyMapField()),
        ('senderClient', 'senderClient', LimitedLengthStringField(max_length=SENDER_CLIENT_FIELD_LIMIT, nullable=True)),
    )

    def __init__(self, request: Message = None, senderClient: str = None) -> None:
        self.request = request
        self.senderClient = senderClient


class Propagate(NodeMessage[PropagateData]):
    typename = "PROPAGATE"
    version = 0
    data_cls = PropagateData

# PRE-PREPARE

class PrePrepare(MessageBase):
    typename = PREPREPARE
    schema = (
        (f.INST_ID.nm, NonNegativeNumberField()),
        (f.VIEW_NO.nm, NonNegativeNumberField()),
        (f.PP_SEQ_NO.nm, NonNegativeNumberField()),
        (f.PP_TIME.nm, TimestampField()),
        (f.REQ_IDR.nm, IterableField(RequestIdentifierField())),
        (f.DISCARDED.nm, NonNegativeNumberField()),
        (f.DIGEST.nm, LimitedLengthStringField(max_length=DIGEST_FIELD_LIMIT)),
        (f.LEDGER_ID.nm, LedgerIdField()),
        (f.STATE_ROOT.nm, MerkleRootField(nullable=True)),
        (f.TXN_ROOT.nm, MerkleRootField(nullable=True)),
        # TODO: support multiple multi-sigs for multiple previous batches
        (f.BLS_MULTI_SIG.nm, BlsMultiSignatureField(optional=True,
                                                    nullable=True)),
        (f.PLUGIN_FIELDS.nm, AnyMapField(optional=True, nullable=True)),
    )


class Prepare(MessageBase):
    typename = PREPARE
    schema = (
        (f.INST_ID.nm, NonNegativeNumberField()),
        (f.VIEW_NO.nm, NonNegativeNumberField()),
        (f.PP_SEQ_NO.nm, NonNegativeNumberField()),
        (f.PP_TIME.nm, TimestampField()),
        (f.DIGEST.nm, LimitedLengthStringField(max_length=DIGEST_FIELD_LIMIT)),
        (f.STATE_ROOT.nm, MerkleRootField(nullable=True)),
        (f.TXN_ROOT.nm, MerkleRootField(nullable=True)),
        (f.PLUGIN_FIELDS.nm, AnyMapField(optional=True, nullable=True))
    )


class Commit(MessageBase):
    typename = COMMIT
    schema = (
        (f.INST_ID.nm, NonNegativeNumberField()),
        (f.VIEW_NO.nm, NonNegativeNumberField()),
        (f.PP_SEQ_NO.nm, NonNegativeNumberField()),
        (f.BLS_SIG.nm, LimitedLengthStringField(max_length=BLS_SIG_LIMIT,
                                                optional=True)),
        # PLUGIN_FIELDS is not used in Commit as of now but adding for
        # consistency
        (f.PLUGIN_FIELDS.nm, AnyMapField(optional=True, nullable=True))
    )


class Checkpoint(MessageBase):
    typename = CHECKPOINT
    schema = (
        (f.INST_ID.nm, NonNegativeNumberField()),
        (f.VIEW_NO.nm, NonNegativeNumberField()),
        (f.SEQ_NO_START.nm, NonNegativeNumberField()),
        (f.SEQ_NO_END.nm, NonNegativeNumberField()),
        (f.DIGEST.nm, LimitedLengthStringField(max_length=DIGEST_FIELD_LIMIT)),
    )


class ThreePCState(MessageBase):
    typename = THREE_PC_STATE
    schema = (
        (f.INST_ID.nm, NonNegativeNumberField()),
        # (f.MSGS.nm, IterableField(ClientMessageValidator(
        #     operation_schema_is_strict=True))),
    )


# TODO implement actual rules
class CheckpointState(MessageBase):
    typename = CHECKPOINT_STATE
    schema = (
        (f.SEQ_NO.nm, AnyValueField()),
        (f.DIGESTS.nm, AnyValueField()),
        (f.DIGEST.nm, AnyValueField()),
        (f.RECEIVED_DIGESTS.nm, AnyValueField()),
        (f.IS_STABLE.nm, AnyValueField())
    )


# TODO implement actual rules
class Reply(MessageBase):
    typename = REPLY
    schema = (
        (f.RESULT.nm, AnyValueField()),
    )


class InstanceChange(MessageBase):
    typename = INSTANCE_CHANGE
    schema = (
        (f.VIEW_NO.nm, NonNegativeNumberField()),
        (f.REASON.nm, NonNegativeNumberField())
    )


class LedgerStatus(MessageBase):
    """
    Purpose: spread status of ledger copy on a specific node.
    When node receives this message and see that it has different
    status of ledger it should reply with LedgerStatus that contains its
    status
    """
    typename = LEDGER_STATUS
    schema = (
        (f.LEDGER_ID.nm, LedgerIdField()),
        (f.TXN_SEQ_NO.nm, NonNegativeNumberField()),
        (f.VIEW_NO.nm, NonNegativeNumberField(nullable=True)),
        (f.PP_SEQ_NO.nm, NonNegativeNumberField(nullable=True)),
        (f.MERKLE_ROOT.nm, MerkleRootField()),
    )


class ConsistencyProof(MessageBase):
    typename = CONSISTENCY_PROOF
    schema = (
        (f.LEDGER_ID.nm, LedgerIdField()),
        (f.SEQ_NO_START.nm, NonNegativeNumberField()),
        (f.SEQ_NO_END.nm, NonNegativeNumberField()),
        (f.VIEW_NO.nm, NonNegativeNumberField()),
        (f.PP_SEQ_NO.nm, NonNegativeNumberField()),
        (f.OLD_MERKLE_ROOT.nm, MerkleRootField()),
        (f.NEW_MERKLE_ROOT.nm, MerkleRootField()),
        (f.HASHES.nm, IterableField(LimitedLengthStringField(max_length=HASH_FIELD_LIMIT))),
    )


class CatchupReq(MessageBase):
    typename = CATCHUP_REQ
    schema = (
        (f.LEDGER_ID.nm, LedgerIdField()),
        (f.SEQ_NO_START.nm, NonNegativeNumberField()),
        (f.SEQ_NO_END.nm, NonNegativeNumberField()),
        (f.CATCHUP_TILL.nm, NonNegativeNumberField()),
    )


class CatchupRep(MessageBase):
    typename = CATCHUP_REP
    schema = (
        (f.LEDGER_ID.nm, LedgerIdField()),
        # TODO: turn on validation, the cause is INDY-388
        # (f.TXNS.nm, MapField(key_field=StringifiedNonNegativeNumberField(),
        #                      value_field=ClientMessageValidator(operation_schema_is_strict=False))),
        (f.TXNS.nm, AnyValueField()),
        (f.CONS_PROOF.nm, IterableField(Base58Field(byte_lengths=(32,)))),
    )


class ViewChangeDone(MessageBase):
    """
    Node sends this kind of message when view change steps done and it is
    ready to switch to the new primary.
    In contrast to 'Primary' message this one does not imply election.
    """
    typename = VIEW_CHANGE_DONE

    schema = (
        # name is nullable because this message can be sent when
        # there were no view changes and instance has no primary yet
        (f.VIEW_NO.nm, NonNegativeNumberField()),
        (f.NAME.nm, LimitedLengthStringField(max_length=NAME_FIELD_LIMIT,
                                             nullable=True)),
        (f.LEDGER_INFO.nm, IterableField(LedgerInfoField()))
    )


class CurrentState(MessageBase):
    """
    Node sends this kind of message for nodes which
    suddenly reconnected (lagged). It contains information about current
    pool state, like view no, primary etc.
    """
    typename = CURRENT_STATE

    schema = (
        (f.VIEW_NO.nm, NonNegativeNumberField()),
        (f.PRIMARY.nm, IterableField(AnyField())),  # ViewChangeDone
    )


"""
The choice to do a generic 'request message' feature instead of a specific
one was debated. It has some pros and some cons. We wrote up the analysis in
http://bit.ly/2uxf6Se. This decision can and should be revisited if we feel a
lot of ongoing dissonance about it. Lovesh, Alex, and Daniel, July 2017
"""


class MessageReq(MessageBase):
    """
    Purpose: ask node for any message
    """
    allowed_types = {LEDGER_STATUS, CONSISTENCY_PROOF, PREPREPARE,
                     PROPAGATE, PREPARE}
    typename = MESSAGE_REQUEST
    schema = (
        (f.MSG_TYPE.nm, ChooseField(values=allowed_types)),
        (f.PARAMS.nm, AnyMapField())
    )


class MessageRep(MessageBase):
    """
    Purpose: respond to a node for any requested message
    """
    # TODO: support a setter for `msg` to create an instance of a type
    # according to `msg_type`
    typename = MESSAGE_RESPONSE
    schema = (
        (f.MSG_TYPE.nm, ChooseField(values=MessageReq.allowed_types)),
        (f.PARAMS.nm, AnyMapField()),
        (f.MSG.nm, AnyField())
    )


ThreePhaseType = (PrePrepare, Prepare, Commit)
ThreePhaseMsg = TypeVar("3PhaseMsg", *ThreePhaseType)

ThreePhaseKey = NamedTuple("ThreePhaseKey", [
    f.VIEW_NO,
    f.PP_SEQ_NO
])


class BatchCommitted(MessageBase):
    """
    Purpose: pass to Observable after each batch is committed
    (so that Observable can propagate the data to Observers using ObservedData msg)
    """
    typename = BATCH_COMMITTED
    schema = (
    #     (f.REQUESTS.nm,
    #      IterableField(ClientMessageValidator(operation_schema_is_strict=True))),
        (f.LEDGER_ID.nm, LedgerIdField()),
        (f.PP_TIME.nm, TimestampField()),
        (f.STATE_ROOT.nm, MerkleRootField()),
        (f.TXN_ROOT.nm, MerkleRootField()),
        (f.SEQ_NO_START.nm, NonNegativeNumberField()),
        (f.SEQ_NO_END.nm, NonNegativeNumberField())
    )


# OBSERVED DATA


class ObservedData(MessageBase):
    """
    Purpose: propagate data from Validators to Observers
    """
    # TODO: support other types
    # TODO: support validation of Msg according to the type
    allowed_types = {BATCH}
    typename = OBSERVED_DATA
    schema = (
        (f.MSG_TYPE.nm, ChooseField(values=allowed_types)),
        (f.MSG.nm, AnyValueField())
    )

    def _validate_message(self, dct):
        msg = dct[f.MSG.nm]
        # TODO: support other types
        expected_type_cls = BatchCommitted
        if isinstance(msg, expected_type_cls):
            return None
        if isinstance(msg, dict):
            expected_type_cls(**msg)
            return None
        self._raise_invalid_fields(
            f.MSG.nm, msg,
            "The message type must be {} ".format(expected_type_cls.typename))
