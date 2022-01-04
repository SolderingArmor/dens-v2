#!/usr/bin/env python3

# ==============================================================================
#
import ever_utils
from   ever_utils import *

class DnsRecordTEST(BaseContract):
    
    def __init__(self, everClient: TonClient, name: str, ownerAddress: str, forceFeeReturnToOwner: bool = False, signer: Signer = None):
        genSigner = generateSigner() if signer is None else signer
        self.CONSTRUCTOR = {"ownerAddress": ownerAddress, "forceFeeReturnToOwner":forceFeeReturnToOwner}
        self.INITDATA    = {"_domainName":stringToHex(name), "_domainCode":getCodeFromTvc("../bin/DnsRecordTEST.tvc")}
        BaseContract.__init__(self, everClient=everClient, contractName="DnsRecordTEST", pubkey=ZERO_PUBKEY, signer=genSigner)

    #========================================
    #
    def changeEndpointAddress(self, msig: Multisig, newAddress: str):
        result = self._callFromMultisig(msig=msig, functionName="changeEndpointAddress", functionParams={"newAddress":newAddress}, value=DIME, flags=1)
        return result

    def changeOwner(self, msig: Multisig, newOwnerAddress: str):
        result = self._callFromMultisig(msig=msig, functionName="changeOwner", functionParams={"newOwnerAddress":newOwnerAddress}, value=DIME, flags=1)
        return result

    def changeRegistrationType(self, msig: Multisig, newType: int):
        result = self._callFromMultisig(msig=msig, functionName="changeRegistrationType", functionParams={"newType":newType}, value=DIME, flags=1)
        return result

    def changeRegistrationPrice(self, msig: Multisig, newPrice: int):
        result = self._callFromMultisig(msig=msig, functionName="changeRegistrationPrice", functionParams={"newPrice":newPrice}, value=DIME, flags=1)
        return result

    def changeComment(self, msig: Multisig, newComment: str):
        result = self._callFromMultisig(msig=msig, functionName="changeComment", functionParams={"newComment":stringToHex(newComment)}, value=DIME, flags=1)
        return result

    def prolongate(self, msig: Multisig):
        result = self._callFromMultisig(msig=msig, functionName="prolongate", functionParams={}, value=DIME*5, flags=1)
        return result

    def claimExpired(self, msig: Multisig, newOwnerAddress: str, forceFeeReturnToOwner: bool = False, value: int = EVER):
        result = self._callFromMultisig(msig=msig, functionName="claimExpired", functionParams={"newOwnerAddress":newOwnerAddress, "forceFeeReturnToOwner":forceFeeReturnToOwner}, value=value, flags=1)
        return result

    def releaseDomain(self, msig: Multisig):
        result = self._callFromMultisig(msig=msig, functionName="releaseDomain", functionParams={}, value=DIME*5, flags=1)
        return result

    def TEST_changeDtExpires(self, msig: Multisig, newDate: int):
        result = self._callFromMultisig(msig=msig, functionName="TEST_changeDtExpires", functionParams={"newDate":newDate}, value=DIME, flags=1)
        return result

    def TEST_selfdestruct(self, msig: Multisig, dest: str):
        result = self._callFromMultisig(msig=msig, functionName="TEST_selfdestruct", functionParams={"dest":dest}, value=DIME, flags=1)
        return result

    #========================================
    #
    def getDomainCode(self):
        result = self._run(functionName="getDomainCode", functionParams={})
        return result

    def canProlongate(self):
        result = self._run(functionName="canProlongate", functionParams={})
        return result

    def isExpired(self):
        result = self._run(functionName="isExpired", functionParams={})
        return result

    def getWhois(self):
        result = self._run(functionName="getWhois", functionParams={})
        return result

    def getEndpointAddress(self):
        result = self._run(functionName="getEndpointAddress", functionParams={})
        return result

# ==============================================================================
# 
