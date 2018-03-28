from electrumx.server.session import ElectrumX
import electrumx.lib.util as util
from electrumx.lib.jsonrpc import RPCError


class LBRYElectrumX(ElectrumX):

    def set_protocol_handlers(self, ptuple):
        super().set_protocol_handlers(ptuple)
        handlers = {'blockchain.transaction.get_height': self.transaction_get_height}
        self.electrumx_handlers.update(handlers)

    async def transaction_get_height(self, tx_hash):
        self.log_info("worked")
        self.assert_tx_hash(tx_hash)
        transaction_info = await self.daemon.getrawtransaction(tx_hash, True)
        if transaction_info and 'hex' in transaction_info and 'confirmations' in transaction_info:
            # an unconfirmed transaction from lbrycrdd will not have a 'confirmations' field
            height = self.bp.db_height
            height = height - transaction_info['confirmations']
            return height
        elif transaction_info and 'hex' in transaction_info:
            return -1
        return None

    def assert_tx_hash(self, value):
        '''Raise an RPCError if the value is not a valid transaction
        hash.'''
        try:
            if len(util.hex_to_bytes(value)) == 32:
                return
        except Exception:
            pass
        raise RPCError('{} should be a transaction hash'.format(value))
