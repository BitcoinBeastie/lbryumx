from electrumx.server.daemon import Daemon


class LBCDaemon(Daemon):

    async def getclaimbyid(self, claim_id):
        '''Given a claim id, retrieves claim information.'''
        return await self._send_single('getclaimbyid', [claim_id])