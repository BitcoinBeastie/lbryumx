from collections import namedtuple
from electrumx.lib.tx import Deserializer
from lbryumx.opcodes import decode_claim_script
from electrumx.lib.util import cachedproperty


class LBRYTx(namedtuple("Tx", "version inputs outputs locktime")):
    '''Transaction that can contain claim, update or support outputs.'''

    @cachedproperty
    def is_coinbase(self):
        return self.inputs[0].is_coinbase

    @cachedproperty
    def has_claims(self):
        for output in self.outputs:
            if output.claim:
                return True
        return False


class TxClaimOutput(namedtuple("TxClaimOutput", "value pk_script claim")):
    pass


class LBRYDeserializer(Deserializer):

    def _read_output(self):
        value = self._read_le_int64()
        script = self._read_varbytes()  # pk_script
        claim = decode_claim_script(script)
        claim = claim[0] if claim else None
        return TxClaimOutput(value, script, claim)

    def read_tx(self):
        return LBRYTx(
            self._read_le_int32(),  # version
            self._read_inputs(),    # inputs
            self._read_outputs(),   # outputs
            self._read_le_uint32()  # locktime
        )
