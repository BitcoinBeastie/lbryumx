from binascii import unhexlify, hexlify

from electrumx.lib.hash import hash_to_str
from electrumx.server.session import ElectrumX
import electrumx.lib.util as util
from electrumx.lib.jsonrpc import RPCError

from lbryumx.block_processor import claim_id_hash


class LBRYElectrumX(ElectrumX):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_protocol_handlers(self, ptuple):
        super().set_protocol_handlers(ptuple)
        handlers = {
            'blockchain.transaction.get_height': self.transaction_get_height,
            'blockchain.claimtrie.getclaimbyid': self.claimtrie_getclaimbyid,
            'blockchain.claimtrie.getclaimsforname': self.claimtrie_getclaimsforname,
            'blockchain.claimtrie.getclaimsbyids': self.claimtrie_getclaimsbyids,
            'blockchain.claimtrie.getvalue': self.claimtrie_getnameproof,
            'blockchain.claimtrie.getnthclaimforname': self.claimtrie_getnthclaimforname,
            'blockchain.claimtrie.getclaimsintx': self.claimtrie_getclaimsintx,
            'blockchain.claimtrie.getclaimssignedby': self.claimtrie_getclaimssignedby,
            'blockchain.claimtrie.getclaimssignedbyid': self.claimtrie_getclaimssignedbyid
        }
        self.electrumx_handlers.update(handlers)

    async def transaction_get_height(self, tx_hash):
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

    async def claimtrie_getclaimssignedby(self, name):
        winning_claim = await self.daemon.getvalueforname(str(name))
        if winning_claim:
            return await self.claimtrie_getclaimssignedbyid(winning_claim['claimId'])

    async def claimtrie_getclaimssignedbyid(self, certificate_id):
        raw_certificate_id = unhexlify(certificate_id)[::-1]
        raw_claim_ids = self.bp.get_signed_claim_ids_by_cert_id(raw_certificate_id)
        claim_ids = map(hash_to_str, raw_claim_ids)
        claims = await self.daemon.getclaimsbyids(claim_ids)
        return list(map(self.format_claim_from_daemon, claims))


    async def claimtrie_getclaimsintx(self, txid):
        # TODO: this needs further discussion.
        # Code on lbryum-server is wrong and we need to gather what we clearly expect from this command
        claim_ids = [claim['claimId'] for claim in (await self.daemon.getclaimsfortx(txid)) if 'claimId' in claim]
        claims = await self.daemon.getclaimsbyids(claim_ids)
        return list(map(self.format_claim_from_daemon, claims))

    async def claimtrie_getnameproof(self, name, block_hash=None):
        proof = await self.daemon.getnameproof(name, block_hash)
        result = {'proof': proof, 'supports': []}

        if proof_has_winning_claim(proof):
            tx_hash, nout = proof['txhash'], int(proof['nOut'])
            transaction_info = await self.daemon.getrawtransaction(tx_hash, True)
            result['transaction'] = transaction_info['hex']
            result['height'] = (self.bp.db_height - transaction_info['confirmations']) + 1
            raw_claim_id = self.bp.get_claim_id_from_outpoint(unhexlify(tx_hash)[::-1], nout)
            result['claim_id'] = claim_id = hexlify(raw_claim_id[::-1]).decode()
            claim_info = await self.daemon.getclaimbyid(claim_id)
            result['claim_sequence'] = self.bp.get_claims_for_name(name.encode('ISO-8859-1'))[raw_claim_id]
            result['supports'] = self.format_supports_from_daemon(claim_info['supports'])
        return result

    async def claimtrie_getnthclaimforname(self, name, n):
        n = int(n)
        for claim_id, sequence in self.bp.get_claims_for_name(name.encode('ISO-8859-1')).items():
            if n == sequence:
                return await self.claimtrie_getclaimbyid(hash_to_str(claim_id))

    async def claimtrie_getclaimsforname(self, name):
        claims = await self.daemon.getclaimsforname(name)
        if claims:
            claims['claims'] = [self.format_claim_from_daemon(claim, name) for claim in claims['claims']]
            claims['supports_without_claims'] = claims['supports without claims']
            del claims['supports without claims']
            claims['last_takeover_height'] = claims['nLastTakeoverHeight']
            del claims['nLastTakeoverHeight']
            return claims
        return {}

    def format_claim_from_daemon(self, claim, name=None):
        '''Changes the returned claim data to the format expected by lbrynet and adds missing fields.'''
        if not claim: return {}
        name = name or claim['name']
        claim_id = claim['claimId']
        raw_claim_id = unhexlify(claim_id)[::-1]
        address = self.bp.get_claim_info(raw_claim_id).address.decode()
        sequence = self.bp.get_claims_for_name(name.encode('ISO-8859-1'))[raw_claim_id]
        supports = self.format_supports_from_daemon(claim['supports'])

        amount = get_from_possible_keys(claim, 'amount', 'nAmount')
        height = get_from_possible_keys(claim, 'height', 'nHeight')
        effective_amount = get_from_possible_keys(claim, 'effective amount', 'nEffectiveAmount')
        valid_at_height = get_from_possible_keys(claim, 'valid at height', 'nValidAtHeight')

        return {
            "name": name,
            "claim_id": claim['claimId'],
            "txid": claim['txid'],
            "nout": claim['n'],
            "amount": amount,
            "depth": self.bp.db_height - height,
            "height": height,
            "value": hexlify(claim['value'].encode('ISO-8859-1')).decode(),
            "claim_sequence": sequence,  # from index
            "address": address,  # from index
            "supports": supports,
            "effective_amount": effective_amount,
            "valid_at_height": valid_at_height  # TODO PR lbrycrd to include it
        }

    def format_supports_from_daemon(self, supports):
        return [[support['txid'], support['n'], get_from_possible_keys(support, 'amount', 'nAmount')] for
                 support in supports]

    async def claimtrie_getclaimbyid(self, claim_id):
        self.assert_claim_id(claim_id)
        claim = await self.daemon.getclaimbyid(claim_id)
        return self.format_claim_from_daemon(claim)

    async def claimtrie_getclaimsbyids(self, *claim_ids):
        claims = await self.daemon.getclaimsbyids(claim_ids)
        return dict((claim_id, self.format_claim_from_daemon(claim),) for claim_id, claim in zip(claim_ids, claims))

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


def proof_has_winning_claim(proof):
    return {'txhash', 'nOut'}.issubset(proof.keys())


def get_from_possible_keys(dictionary, *keys):
    for key in keys:
        if key in dictionary:
            return dictionary[key]
