from trezor.messages.TxOutputType import TxOutputType

from .bitcoin import Bitcoin


class CoinJoin(Bitcoin):
    async def confirm_output(self, txo: TxOutputType, script_pubkey: bytes) -> None:
        # Consider all outputs confirmed and allow multiple change addresses.

        if self.output_is_change(txo):
            self.change_out += txo.amount

        self.write_tx_output(self.h_confirmed, txo, script_pubkey)
        self.hash143_add_output(txo, script_pubkey)
        self.total_out += txo.amount
