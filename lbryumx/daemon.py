from electrumx.server.daemon import Daemon


class LBCDaemon(Daemon):

    async def getclaimbyid(self, claim_id):
        '''Given a claim id, retrieves claim information.'''
        return await self._send_single('getclaimbyid', (claim_id,))

    async def getclaimsbyids(self, claim_ids):
        '''Given a list of claim ids, batches calls to retrieve claim information.'''
        return await self._send_vector('getclaimbyid', ((claim_id,) for claim_id in claim_ids))

    async def getclaimsforname(self, name):
        '''Given a name, retrieves all claims matching that name.'''
        return await self._send_single('getclaimsforname', (name,))

    async def getclaimsfortx(self, txid):
        '''Given a txid, returns the claims it make.'''
        return await self._send_single('getclaimsfortx', (txid,))

    async def getnameproof(self, name, block_hash=None):
        '''Given a name and optional block_hash, returns a name proof and winner, if any.'''
        return await self._send_single('getnameproof', (name, block_hash,) if block_hash else (name,))

    async def getvalueforname(self, name):
        '''Given a name, returns the winning claim value.'''
        return await self._send_single('getvalueforname', (name,))
