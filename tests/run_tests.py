#!/usr/bin/env python3

# ==============================================================================
# 
from freeton_utils import *
import unittest
import sys

TON = 1000000000

# ==============================================================================
# 
# Parse arguments and then clear them because UnitTest will @#$~!
CUSTOM_URL = ""
USE_GIVER  = True
THROW      = False

for i, arg in enumerate(sys.argv[1:]):
    if arg == "--disable-giver":
        USE_GIVER = False
        sys.argv.remove(arg)
    if arg == "--throw":
        THROW = True
        sys.argv.remove(arg)
    elif arg.startswith("http"):
        CUSTOM_URL = arg
        sys.argv.remove(arg)

changeConfig(CUSTOM_URL, USE_GIVER, THROW)

# ==============================================================================
# 
def createDomainDictionary(name):

    ABI  = "../bin/DnsRecordTEST.abi.json"
    TVC  = "../bin/DnsRecordTEST.tvc"
    CODE = getCodeFromTvc(TVC)
    INIT = {"_domainName":stringToHex(name),"_domainCode": CODE}
    
    domainDictionary = {
        "NAME":   name,
        "DOMAIN": stringToHex(name),
        "ABI":    ABI,
        "TVC":    TVC,
        "CODE":   CODE,
        "INIT":   INIT,
        "ADDR":   getAddressZeroPubkey(abiPath=ABI, tvcPath=TVC, initialData=INIT)
    }
    return domainDictionary

# ==============================================================================
# 
def createMultisigDictionary(pubkey):

    ABI         = "../bin/SetcodeMultisigWallet.abi.json"
    TVC         = "../bin/SetcodeMultisigWallet.tvc"
    CONSTRUCTOR = {"owners":["0x" + pubkey],"reqConfirms":"1"}
    SIGNER      = Signer.External(public_key=pubkey)

    multisigDictionary = {
        "PUBKEY": pubkey,
        "ABI":    ABI,
        "TVC":    TVC,
        "CONSTR": CONSTRUCTOR,
        "ADDR":   getAddress(abiPath=ABI, tvcPath=TVC, signer=SIGNER, initialPubkey=pubkey, initialData={})
    }
    return multisigDictionary

# ==============================================================================
# DOMAIN MANAGEMENT
#
def deployDomain(domainDict, ownerID, signer):
    result = deployContract(abiPath=domainDict["ABI"], tvcPath=domainDict["TVC"], constructorInput={"ownerID":ownerID}, initialData=domainDict["INIT"], signer=signer, initialPubkey=ZERO_PUBKEY)
    return result

def callDomainFunction(domainDict, functionName, functionParams, signer):
    result = callFunction(abiPath=domainDict["ABI"], contractAddress=domainDict["ADDR"], functionName=functionName, functionParams=functionParams, signer=signer)
    return result

def runDomainFunction(domainDict, functionName, functionParams):
    result = runFunction(abiPath=domainDict["ABI"], contractAddress=domainDict["ADDR"], functionName=functionName, functionParams=functionParams)
    return result

# ==============================================================================
# MULTISIG MANAGEMENT
# 
def deployMultisig(msigDict, signer):
    result = deployContract(abiPath=msigDict["ABI"], tvcPath=msigDict["TVC"], constructorInput=msigDict["CONSTR"], initialData={}, signer=signer, initialPubkey=signer.keys.public)
    return result

def callMultisigFunction(msigDict, functionName, functionParams, signer):
    result = callFunction(abiPath=msigDict["ABI"], contractAddress=msigDict["ADDR"], functionName=functionName, functionParams=functionParams, signer=signer)
    return result

def callMultisigFunctionTransfer(msigDict, addressDest, value, payload, flags, signer):
    result = callMultisigFunction(msigDict, "sendTransaction", {"dest":addressDest, "value":value, "bounce":False, "flags":flags, "payload":payload}, signer)
    return result

def runMultisigFunction(msigDict, functionName, functionParams):
    result = runFunction(abiPath=msigDict["ABI"], contractAddress=msigDict["ADDR"], functionName=functionName, functionParams=functionParams)
    return result

# ==============================================================================
# MULTISIG TO DOMAIN MANAGEMENT
# 
def callDomainFunctionFromMultisig(domainDict, msigDict, functionName, functionParams, value, flags, signer):

    callSet = CallSet(function_name=functionName, input=functionParams)
    params  = ParamsOfEncodeMessageBody(abi=getAbi(domainDict["ABI"]), signer=Signer.NoSigner(), is_internal=True, call_set=callSet)
    encoded = asyncClient.abi.encode_message_body(params=params)

    result = callMultisigFunctionTransfer(msigDict=msigDict, addressDest=domainDict["ADDR"], value=value, payload=encoded.body, flags=flags, signer=signer)
    return result

# ==============================================================================
# 
class Test_1_SameNameDeploy(unittest.TestCase):

    domain = createDomainDictionary("org")
    signer = generateSigner()
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain["ADDR"], TON * 2)

    # 2. Deploy "org"
    def test_2(self):
        result = deployDomain(domainDict=self.domain, ownerID=0, signer=self.signer)
        self.assertEqual(result[1], 0)

    # 3. Deploy "org" once again
    def test_3(self):
        result = deployDomain(domainDict=self.domain, ownerID=0, signer=self.signer)
        self.assertEqual(result[1], 51)

    # 4. Cleanup
    def test_4(self):
        result = callDomainFunction(domainDict=self.domain, functionName="TEST_selfdestruct", functionParams={}, signer=self.signer)
        self.assertEqual(result[1], 0)

# ==============================================================================
#
class Test_2_DeployWithMultisigOwner(unittest.TestCase):
    
    signerD = generateSigner()
    signerM = generateSigner()
    domain  = createDomainDictionary("net")
    msig    = createMultisigDictionary(signerM.keys.public)
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain["ADDR"], TON * 2 )
        giverGive(self.msig  ["ADDR"], TON * 20)
        
    # 2. Deploy multisig
    def test_2(self):
        result = deployMultisig(self.msig, self.signerM)
        self.assertEqual(result[1], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = deployDomain(self.domain, 0, self.signerD)
        self.assertEqual(result[1], 0)

    # 4. Call change endpoint from multisig
    def test_4(self):
        endpoint = "0:78bf2beea2cd6ff9c78b0aca30e00fa627984dc01ad0351915002051d425f1e4"
        result   = callDomainFunctionFromMultisig(domainDict=self.domain, msigDict=self.msig, functionName="changeEndpointAddress", functionParams={"newAddress":endpoint}, value=100000000, flags=1, signer=self.signerM)
        self.assertEqual(result[1], 0)

        result   = runDomainFunction(domainDict=self.domain, functionName="getEndpointAddress", functionParams={})
        self.assertEqual(result, endpoint)

    # 5. Cleanup
    def test_5(self):
        result = callDomainFunction(domainDict=self.domain, functionName="TEST_selfdestruct", functionParams={}, signer=self.signerD)
        self.assertEqual(result[1], 0)


# ==============================================================================
# 
unittest.main()
exit()

# ==============================================================================
# Decode custom BOC using ABI 
#
#boc = "te6ccgEBAQEAKAAAS2t6vFCADxflfdRZrf848WFZRhwB9MTzCbgDWgajIqAECjqEvjyQ"
#params = ParamsOfDecodeMessageBody(abi=getAbi("../bin/DnsRecordTEST.abi.json"), body=boc, is_internal=True)
#result = asyncClient.abi.decode_message_body(params=params)

#print(result.body_type, result.value, result.name, result.header)
#exit()
