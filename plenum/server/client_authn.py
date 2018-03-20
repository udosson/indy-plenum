"""
Clients are authenticated with a digital signature.
"""
from abc import abstractmethod
from typing import Dict

import base58

from plenum.common.constants import VERKEY, ROLE, GET_TXN
from plenum.common.exceptions import CouldNotAuthenticate, \
    InvalidSignatureFormat, UnknownIdentifier, \
    InsufficientSignatures, InsufficientCorrectSignatures
from plenum.common.verifier import DidVerifier, Verifier
from plenum.server.domain_req_handler import DomainRequestHandler
from plenum.server.pool_req_handler import PoolRequestHandler
from stp_core.common.log import getlogger

logger = getlogger()


class ClientAuthNr:
    """
    Interface for client authenticators.
    """

    @abstractmethod
    def authenticate(self,
                     msg: bytes,
                     signatures: Dict[str, str],
                     threshold: int = None):
        """
        :param msg:
        :param signatures: A mapping from identifiers to signatures.
        :param threshold: The number of successful signature verification
        required. By default all signatures are required to be verified.
        :return: returns the identifiers whose signature was matched and
        correct; a SigningException is raised if threshold was not met
        """

    @abstractmethod
    def addIdr(self, identifier, verkey, role=None):
        """
        Adding an identifier should be an auditable and authenticated action.
        Robust implementations of ClientAuthNr would authenticate this
        operation.

        :param identifier: an identifier that directly or indirectly identifies
            a client
        :param verkey: the public key used to verify a signature
        :return: None
        """

    @abstractmethod
    def getVerkey(self, identifier):
        """
        Get the verification key for a client based on the client's identifier

        :param identifier: client's identifier
        :return: the verification key
        """


class NaclAuthNr(ClientAuthNr):
    def authenticate(self,
                     msg: bytes,
                     signatures: Dict[str, str],
                     threshold: int = None,
                     verifier: Verifier = DidVerifier):
        num_sigs = len(signatures)
        if threshold is not None:
            if num_sigs < threshold:
                raise InsufficientSignatures(num_sigs, threshold)
        else:
            threshold = num_sigs
        correct_sigs_from = []
        for idr, sig in signatures.items():
            try:
                sig = base58.b58decode(sig)
            except Exception as ex:
                raise InvalidSignatureFormat from ex

            verkey = self.getVerkey(idr)

            if verkey is None:
                raise CouldNotAuthenticate(
                    'Can not find verkey for {}'.format(idr))

            vr = verifier(verkey, identifier=idr)
            if vr.verify(sig, msg):
                correct_sigs_from.append(idr)
                if len(correct_sigs_from) == threshold:
                    break
        else:
            raise InsufficientCorrectSignatures(len(correct_sigs_from),
                                                threshold)
        return correct_sigs_from

    @abstractmethod
    def addIdr(self, identifier, verkey, role=None):
        pass

    @abstractmethod
    def getVerkey(self, identifier):
        pass


class SimpleAuthNr(NaclAuthNr):
    """
    Simple client authenticator. Should be replaced with a more robust and
    secure system.
    """

    def __init__(self, state=None):
        # key: some identifier, value: verification key
        self.clients = {}  # type: Dict[str, Dict]
        self.state = state

    def addIdr(self, identifier, verkey, role=None):
        if identifier in self.clients:
            # raise RuntimeError("client already added")
            logger.debug("client already added")
        self.clients[identifier] = {
            VERKEY: verkey,
            ROLE: role
        }

    def getVerkey(self, identifier):
        nym = self.clients.get(identifier)
        if not nym:
            # Querying uncommitted identities since a batch might contain
            # both identity creation request and a request by that newly
            # created identity, also its possible to have multiple uncommitted
            # batches in progress and identity creation request might
            # still be in an earlier uncommited batch
            nym = DomainRequestHandler.getNymDetails(
                self.state, identifier, isCommitted=False)
            if not nym:
                raise UnknownIdentifier(identifier)
        return nym.get(VERKEY)


class CoreAuthMixin:
    write_types = PoolRequestHandler.write_types.union(
        DomainRequestHandler.write_types
    )
    query_types = {GET_TXN, }.union(
        PoolRequestHandler.query_types
    ).union(
        DomainRequestHandler.query_types
    )

    @classmethod
    def is_query(cls, typ):
        return typ in cls.query_types

    @classmethod
    def is_write(cls, typ):
        return typ in cls.write_types


class CoreAuthNr(CoreAuthMixin, SimpleAuthNr):
    def __init__(self, state=None):
        SimpleAuthNr.__init__(self, state)
        CoreAuthMixin.__init__(self)
