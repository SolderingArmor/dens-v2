#!/usr/bin/env python3

# ==============================================================================
#
import freeton_utils
from   freeton_utils import *

class DnsDebotTEST(object):
    def __init__(self, signer: Signer):
        self.SIGNER      = generateSigner() if signer is None else signer
        self.ABI         = "../bin/DnsDebotTEST.abi.json"
        self.TVC         = "../bin/DnsDebotTEST.tvc"
        self.CODE        = getCodeFromTvc("../bin/DnsRecordTEST.tvc")
        self.CONSTRUCTOR = {}
        self.INITDATA    = {"_domainCode": self.CODE}
        self.PUBKEY      = signer.keys.public
        self.ADDRESS     = getAddress(abiPath=self.ABI, tvcPath=self.TVC, signer=signer, initialPubkey=self.PUBKEY, initialData=self.INITDATA)

    def deploy(self):
        result = deployContract(abiPath=self.ABI, tvcPath=self.TVC, constructorInput=self.CONSTRUCTOR, initialData=self.INITDATA, signer=self.SIGNER, initialPubkey=self.PUBKEY)
        return result
    
    def call(self, functionName, functionParams, signer):
        result = callFunction(abiPath=self.ABI, contractAddress=self.ADDRESS, functionName=functionName, functionParams=functionParams, signer=signer)
        return result

    def callFromMultisig(self, msig: SetcodeMultisig, functionName, functionParams, value, flags):
        messageBoc = prepareMessageBoc(abiPath=self.ABI, functionName=functionName, functionParams=functionParams)
        result     = msig.callTransfer(addressDest=self.ADDRESS, value=value, payload=messageBoc, flags=flags)
        return result

# ==============================================================================
# 
