#!/usr/bin/env python3

# ==============================================================================
#
import freeton_utils
from   freeton_utils import *

class DnsRecord(object):
    def __init__(self, name: str, signer: Signer = None):
        self.SIGNER      = generateSigner() if signer is None else signer
        self.ABI         = "../bin/DnsRecord.abi.json"
        self.TVC         = "../bin/DnsRecord.tvc"
        self.CODE        = getCodeFromTvc(self.TVC)
        self.CONSTRUCTOR = {}
        self.INITDATA    = {"_domainName":stringToHex(name),"_domainCode": self.CODE}
        self.PUBKEY      = ZERO_PUBKEY
        self.ADDRESS     = getAddressZeroPubkey(abiPath=self.ABI, tvcPath=self.TVC, initialData=self.INITDATA)

    def deploy(self, ownerAddress: str):
        self.CONSTRUCTOR = {"ownerAddress": ownerAddress}
        result = deployContract(abiPath=self.ABI, tvcPath=self.TVC, constructorInput=self.CONSTRUCTOR, initialData=self.INITDATA, signer=self.SIGNER, initialPubkey=self.PUBKEY)
        return result

    def call(self, functionName, functionParams, signer):
        result = callFunction(abiPath=self.ABI, contractAddress=self.ADDRESS, functionName=functionName, functionParams=functionParams, signer=signer)
        return result

    def callFromMultisig(self, msig: SetcodeMultisig, functionName, functionParams, value, flags):
        messageBoc = prepareMessageBoc(abiPath=self.ABI, functionName=functionName, functionParams=functionParams)
        result     = msig.callTransfer(addressDest=self.ADDRESS, value=value, payload=messageBoc, flags=flags)
        return result

    def run(self, functionName, functionParams):
        result = runFunction(abiPath=self.ABI, contractAddress=self.ADDRESS, functionName=functionName, functionParams=functionParams)
        return result

    def destroy(self, addressDest):
        result = self.call(functionName="TEST_selfdestruct", functionParams={"dest":freeton_utils.giverGetAddress()}, signer=self.SIGNER)
        return result

# ==============================================================================
# 
