import utime
from micropython import const

from .common import BIP32_WALLET_DEPTH

if False:
    from typing import Optional
    from trezor.messages.AuthorizeCoinJoin import AuthorizeCoinJoin
    from trezor.messages.GetOwnershipProof import GetOwnershipProof
    from apps.common import coininfo


_ROUND_ID_LEN = const(8)
_ROUND_ID_LIFETIME_MS = const(
    10 * 60 * 1000
)  # 10 minutes before a proof of ownership can be generated for another round ID

_coinjoin_authorization = None  # type: Optional[CoinJoinAuthorization]


class CoinJoinAuthorization:
    def __init__(self, msg: AuthorizeCoinJoin, coin: coininfo.CoinInfo):
        self.amount = msg.amount
        self.max_fee = msg.max_fee
        self.coordinator = msg.coordinator
        self.round_id = bytes()
        self.round_id_expiry = 0
        self.address_n = msg.address_n
        self.coin = coin
        self.script_type = msg.script_type

    def confirm_get_ownership_proof(self, msg: GetOwnershipProof) -> bool:
        # Check whether the current authorization matches the parameters of the request.
        if (
            msg.address_n[:-BIP32_WALLET_DEPTH] != self.address_n
            or msg.coin_name != self.coin.coin_name
            or msg.script_type != self.script_type
            or len(msg.commitment_data) < _ROUND_ID_LEN
            or msg.commitment_data[:-_ROUND_ID_LEN] != self.coordinator.encode()
        ):
            return False

        # Allow changing to a different round ID only after _ROUND_ID_LIFETIME_MS.

        round_id = msg.commitment_data[-_ROUND_ID_LEN:]
        if round_id == self.round_id:
            return True

        if self.round_id_expiry <= utime.ticks_ms():
            self.round_id = round_id
            self.round_id_expiry = utime.ticks_ms() + _ROUND_ID_LIFETIME_MS
            return True

        return False


def set_coinjoin_authorization(msg: AuthorizeCoinJoin, coin: coininfo.CoinInfo):
    global _coinjoin_authorization
    _coinjoin_authorization = CoinJoinAuthorization(msg, coin)


def confirm_get_ownership_proof(msg: GetOwnershipProof) -> bool:
    if _coinjoin_authorization:
        return _coinjoin_authorization.confirm_get_ownership_proof(msg)

    return False
