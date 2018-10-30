from asyncio import Event

from aiorpcx import _version as aiorpcx_version, TaskGroup
from electrumx.lib.util import version_string
from electrumx.server.controller import Controller, Notifications
from electrumx.server.mempool import MemPool, MemPoolAPI
from electrumx.server.session import SessionManager
from electrumx.server.db import DB

from lbryumx.db import LBRYDB


class LBRYController(Controller):
    async def serve(self, shutdown_event):
        '''Start the RPC server and wait for the mempool to synchronize.  Then
        start serving external clients.
        '''
        if not (0, 9, 0) <= aiorpcx_version < (0, 10):
            raise RuntimeError('aiorpcX version 0.9.x required')

        env = self.env
        min_str, max_str = env.coin.SESSIONCLS.protocol_min_max_strings()
        self.logger.info(f'aiorpcX version: {version_string(aiorpcx_version)}')
        self.logger.info(f'supported protocol versions: {min_str}-{max_str}')
        self.logger.info(f'event loop policy: {env.loop_policy}')
        self.logger.info(f'reorg limit is {env.reorg_limit:,d} blocks')

        notifications = Notifications()
        Daemon = env.coin.DAEMON
        BlockProcessor = env.coin.BLOCK_PROCESSOR

        daemon = Daemon(env.coin, env.daemon_url)
        db = LBRYDB(env) if env.coin.NAME == 'LBRY' else DB(env)
        bp = BlockProcessor(env, db, daemon, notifications)

        # Set notifications up to implement the MemPoolAPI
        notifications.height = daemon.height
        notifications.cached_height = daemon.cached_height
        notifications.mempool_hashes = daemon.mempool_hashes
        notifications.raw_transactions = daemon.getrawtransactions
        notifications.lookup_utxos = db.lookup_utxos
        MemPoolAPI.register(Notifications)
        mempool = MemPool(env.coin, notifications)

        session_mgr = SessionManager(env, db, bp, daemon, mempool,
                                     shutdown_event)

        # Test daemon authentication, and also ensure it has a cached
        # height.  Do this before entering the task group.
        await daemon.height()

        caught_up_event = Event()
        mempool_event = Event()

        async def wait_for_catchup():
            await caught_up_event.wait()
            await group.spawn(db.populate_header_merkle_cache())
            await group.spawn(mempool.keep_synchronized(mempool_event))

        async with TaskGroup() as group:
            await group.spawn(session_mgr.serve(notifications, mempool_event))
            await group.spawn(bp.fetch_and_process_blocks(caught_up_event))
            await group.spawn(wait_for_catchup())

