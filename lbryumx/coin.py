import struct

from electrumx.lib.hash import hash_to_str
from electrumx.lib.coins import Coin, CoinError


class LBC(Coin):
    from lbryumx.session import LBRYElectrumX
    from lbryumx.block_processor import LBRYBlockProcessor
    from lbryumx.tx import LBRYDeserializer
    SESSIONCLS = LBRYElectrumX
    BLOCK_PROCESSOR = LBRYBlockProcessor
    DESERIALIZER = LBRYDeserializer
    NAME = "LBRY"
    SHORTNAME = "LBC"
    NET = "mainnet"
    BASIC_HEADER_SIZE = 112
    CHUNK_SIZE = 96
    XPUB_VERBYTES = bytes.fromhex("0488b21e")
    XPRV_VERBYTES = bytes.fromhex("0488ade4")
    P2PKH_VERBYTE = bytes.fromhex("55")
    P2SH_VERBYTES = bytes.fromhex("7A")
    WIF_BYTE = bytes.fromhex("1C")
    GENESIS_HASH = ('9c89283ba0f3227f6c03b70216b9f665'
                    'f0118d5e0fa729cedf4fb34d6a34f463')
    TX_COUNT = 2716936
    TX_COUNT_HEIGHT = 329554
    TX_PER_BLOCK = 1
    RPC_PORT = 9245
    REORG_LIMIT = 200
    PEERS = [
        'lbryum8.lbry.io t',
        'lbryum9.lbry.io t',
    ]

    @classmethod
    def genesis_block(cls, block):
        '''Check the Genesis block is the right one for this coin.

        Return the block less its unspendable coinbase.
        '''
        header = cls.block_header(block, 0)
        header_hex_hash = hash_to_str(cls.header_hash(header))
        if header_hex_hash != cls.GENESIS_HASH:
            raise CoinError('genesis block has hash {} expected {}'
                            .format(header_hex_hash, cls.GENESIS_HASH))

        return block

    @classmethod
    def electrum_header(cls, header, height):
        version, = struct.unpack('<I', header[:4])
        timestamp, bits, nonce = struct.unpack('<III', header[100:112])
        return {
            'version': version,
            'prev_block_hash': hash_to_str(header[4:36]),
            'merkle_root': hash_to_str(header[36:68]),
            'claim_trie_root': hash_to_str(header[68:100]),
            'timestamp': timestamp,
            'bits': bits,
            'nonce': nonce,
            'block_height': height,
            }
