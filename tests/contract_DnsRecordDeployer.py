#!/usr/bin/env python3

# ==============================================================================
#
import freeton_utils
from   freeton_utils import *

class DnsRecordDeployer(object):
    def __init__(self, signer: Signer = None):
        self.SIGNER      = generateSigner() if signer is None else signer
        self.ABI         = "../bin/DnsRecordDeployer.abi.json"
        self.TVC         = "../bin/DnsRecordDeployer.tvc"
        self.CODE        = getCodeFromTvc("../bin/DnsRecordTEST.tvc")
        self.CONSTRUCTOR = {}
        self.INITDATA    = {"_domainCode": self.CODE}
        self.PUBKEY      = ZERO_PUBKEY
        self.ADDRESS     = getAddressZeroPubkey(abiPath=self.ABI, tvcPath=self.TVC, initialData=self.INITDATA)

    def deploy(self):
        result = deployContract(abiPath=self.ABI, tvcPath=self.TVC, constructorInput=self.CONSTRUCTOR, initialData=self.INITDATA, signer=self.SIGNER, initialPubkey=self.PUBKEY)
        return result

    def callFromMultisig(self, msig: SetcodeMultisig, functionName, functionParams, value, flags):
        messageBoc = prepareMessageBoc(abiPath=self.ABI, functionName=functionName, functionParams=functionParams)
        result     = msig.callTransfer(addressDest=self.ADDRESS, value=value, payload=messageBoc, flags=flags)
        return result

# ==============================================================================
# 
