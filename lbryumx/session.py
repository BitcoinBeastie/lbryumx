from binascii import unhexlify, hexlify

from electrumx.server.session import ElectrumX
import electrumx.lib.util as util
from electrumx.lib.jsonrpc import RPCError


class LBRYElectrumX(ElectrumX):

    def set_protocol_handlers(self, ptuple):
        super().set_protocol_handlers(ptuple)
        handlers = {
            'blockchain.transaction.get_height': self.transaction_get_height,
            'blockchain.claimtrie.getclaimbyid': self.claimtrie_getclaimbyid
        }
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

    async def claimtrie_getclaimbyid(self, claim_id):
        self.assert_claim_id(claim_id)
        claim = self.daemon.getclaimbyid(claim_id)
        raw_claim_id = unhexlify(claim_id)[::-1]
        claim_info = self.bp.get_claim_info(raw_claim_id)
        claim = await claim
        sequence = self.bp.get_claims_for_name(claim['name'].encode('ISO-8859-1'))[raw_claim_id]
        result = {
            "name": claim['name'],
            "claim_id": claim['claimId'],
            "txid": claim['txid'],
            "nout": claim['n'],
            "amount": claim['amount'],
            "depth": self.bp.db_height - claim['height'],
            "height": claim['height'],
            "value": hexlify(claim['value'].encode('ISO-8859-1')).decode(),
            "claim_sequence": sequence,  # grab from index
            "address": claim_info.address.decode(),  # grab from index
            "supports": claim['supports'],
            "effective_amount": claim['effective amount'],
            "valid_at_height": claim['valid at height']  # TODO PR into lbrycrd to include it
        }
        return result


    def assert_tx_hash(self, value):
        '''Raise an RPCError if the value is not a valid transaction
        hash.'''
        try:
            if len(util.hex_to_bytes(value)) == 32:
                return
        except Exception:
            pass
        raise RPCError('{} should be a transaction hash'.format(value))

    def assert_claim_id(self, value):
        '''Raise an RPCError if the value is not a valid claim id
        hash.'''
        try:
            if len(util.hex_to_bytes(value)) == 20:
                return
        except Exception:
            pass
        raise RPCError('{} should be a claim id hash'.format(value))
