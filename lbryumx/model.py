from collections import namedtuple
from electrumx.lib.util import cachedproperty
# Classes representing data and their serializers, if any.


class NameClaim(namedtuple("NameClaim", "name value")):
    pass


class ClaimUpdate(namedtuple("ClaimUpdate", "name claim_id value")):
    pass


class ClaimSupport(namedtuple("ClaimSupport", "name claim_id")):
    pass


class LBRYTx(namedtuple("Tx", "version inputs outputs locktime")):
    '''Transaction that can contain claim, update or support in its outputs.'''

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
