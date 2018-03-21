from typing import Optional

from plenum.common.constants import TXN_TYPE
from common.error import error
from plenum.common.exceptions import NoAuthenticatorFound
from plenum.common.messages.message import Message, SignedMessage
from plenum.common.types import OPERATION
from plenum.server.client_authn import ClientAuthNr


class MessageAuthenticator:
    """
    Maintains a list of authenticators. The first authenticator in the list
    of authenticators is the core authenticator
    """
    def __init__(self):
        self._authenticators = []

    def register_authenticator(self, authenticator: ClientAuthNr):
        self._authenticators.append(authenticator)

    def authenticate(self, msg: Message):
        """
        Authenticates a given message data by verifying signatures from
        any registered authenticators. If the request is a query returns
        immediately, if no registered authenticator can authenticate then an
        exception is raised.
        :param req_data:
        :return:
        """
        identifiers = set()
        typ = msg.typename
        msg_payload = msg.msg_serialized
        signatures = {v.frm: v.value for v in msg.signature.values}
        threshold = msg.signature.threshold

        for authenticator in self._authenticators:
            if authenticator.is_query(typ):
                return set()
            if not authenticator.is_write(typ):
                continue
            rv = authenticator.authenticate(msg_payload, signatures, threshold) or set()
            identifiers.update(rv)

        if not identifiers:
            raise NoAuthenticatorFound
        return identifiers

    @property
    def core_authenticator(self):
        if not self._authenticators:
            error('No authenticator registered yet', RuntimeError)
        return self._authenticators[0]

    def get_authnr_by_type(self, authnr_type) -> Optional[ClientAuthNr]:
        for authnr in self._authenticators:
            if isinstance(authnr, authnr_type):
                return authnr
