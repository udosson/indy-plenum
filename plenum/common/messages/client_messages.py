from typing import List

from plenum.common.constants import VALIDATOR
from plenum.common.messages.fields import NetworkIpAddressField, \
    NetworkPortField, IterableField, \
    ChooseField, VerkeyField, RoleField, TxnSeqNoField, IdentifierField, \
    LimitedLengthStringField, \
    LedgerIdField, Base58Field
from plenum.common.messages.message import MessageData
from plenum.common.messages.message_base import MessageValidator
from plenum.common.messages.request import Request
from plenum.common.messages.signed_message import SignedMessage
from plenum.common.transactions import PlenumTransactions
from plenum.config import ALIAS_FIELD_LIMIT


# NYM

class NymRequestData(MessageData):
    schema = (
        ('alias', 'alias', LimitedLengthStringField(max_length=ALIAS_FIELD_LIMIT, optional=True)),
        ('verkey', 'verkey', VerkeyField(optional=True, nullable=True)),
        ('did', 'did', IdentifierField()),
        ('role', 'role', RoleField(optional=True)),
        # TODO: validate role using ChooseField,
        # do roles list expandable form outer context
    )

    def __init__(self, alias: str = None, verkey: str = None, did: str = None,
                 role: str = None) -> None:
        self.alias = alias
        self.verkey = verkey
        self.did = did
        self.role = role


class NymRequest(Request[NymRequestData]):
    typename = PlenumTransactions.NYM.value
    version = 0
    data_cls = NymRequestData
    need_signature = True


class SignedNymRequest(SignedMessage[NymRequest]):
    typename = PlenumTransactions.NYM.value
    version = 0
    msg_cls = NymRequest


# NODE

class NodeRequestData(MessageData):
    schema = (
        ('alias', 'alias', LimitedLengthStringField(max_length=ALIAS_FIELD_LIMIT)),
        ('did', 'did', IdentifierField()),
        ('verkey', 'verkey', VerkeyField(optional=True, nullable=True)),
        ('node_ip', 'nodeIp', NetworkIpAddressField(optional=True)),
        ('node_port', 'nodePort', NetworkPortField(optional=True)),
        ('client_ip', 'clientIp', NetworkIpAddressField(optional=True)),
        ('client_port', 'clientPort', NetworkPortField(optional=True)),
        ('services', 'services', IterableField(ChooseField(values=(VALIDATOR,)), optional=True)),
        ('blskey', 'blskey', Base58Field(byte_lengths=(128,), optional=True)),
    )

    def __init__(self, alias: str = None, did: str = None, verkey: str = None,
                 node_ip: str = None, node_port: int = None,
                 client_ip: str = None, client_port: int = None,
                 services: List[str] = None, blskey: str = None) -> None:
        self.alias = alias
        self.did = did
        self.verkey = verkey
        self.node_ip = node_ip
        self.node_port = node_port
        self.client_ip = client_ip
        self.client_port = client_port
        self.services = services
        self.blskey = blskey

    def _validate_message(self, dct):
        # TODO: make ha fields truly optional (needs changes in stackHaChanged)
        required_ha_fields = {'nodeIp', 'nodePort', 'clientIp', 'clientPort'}
        ha_fields = {f for f in required_ha_fields if f in dct}
        if ha_fields and len(ha_fields) != len(required_ha_fields):
            self._raise_missed_fields(*list(required_ha_fields - ha_fields))


class NodeRequest(Request[NodeRequestData]):
    typename = PlenumTransactions.NODE.value
    version = 0
    data_cls = NodeRequestData
    need_signature = True


class SignedNodeRequest(SignedMessage[NodeRequest]):
    typename = PlenumTransactions.NODE.value
    version = 0
    msg_cls = NodeRequest


# GET_TXN


class GetTxnRequestData(MessageValidator):
    schema = (
        ('ledgerId', 'ledgerId', LedgerIdField(optional=True)),
        ('seqNo', 'seqNo', TxnSeqNoField()),
    )


class GetTxnRequest(Request[GetTxnRequestData]):
    typename = PlenumTransactions.GET_TXN.value
    version = 0
    data_cls = GetTxnRequestData
