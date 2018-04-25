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
