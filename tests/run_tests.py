#!/usr/bin/env python3

# ==============================================================================
# 
from freeton_utils import *
import unittest
import time
import sys
import pprint

TON = 1000000000
transactionFilters = "out_msgs, aborted, compute{exit_arg, exit_code, skipped_reason, skipped_reason_name}"

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
class Test_01_SameNameDeploy(unittest.TestCase):

    signer = generateSigner()
    domain = createDomainDictionary("org")
    
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
class Test_02_DeployWithMultisigOwner(unittest.TestCase):
    
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
        result = deployDomain(self.domain, "0x" + self.msig["ADDR"][2:], self.signerD)
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
class Test_03_WrongNames(unittest.TestCase):
    
    signer = generateSigner()
    domainDictList = [
        {"CODE": 0,   "DOMAIN": createDomainDictionary("org-org")},
        {"CODE": 200, "DOMAIN": createDomainDictionary("ORG")},
        {"CODE": 200, "DOMAIN": createDomainDictionary("F@!#ING")},
        {"CODE": 200, "DOMAIN": createDomainDictionary("ddd//dd")},
        {"CODE": 200, "DOMAIN": createDomainDictionary("//")},
        {"CODE": 200, "DOMAIN": createDomainDictionary("")},
        {"CODE": 200, "DOMAIN": createDomainDictionary("under_score")},
        {"CODE": 0,   "DOMAIN": createDomainDictionary("good-domain-name-with-31-letter")},
        {"CODE": 200, "DOMAIN": createDomainDictionary("perfectly000fine000domain000name000with63letters000inside000kek")},
        {"CODE": 0,   "DOMAIN": createDomainDictionary("one/two/three/four")},
        {"CODE": 200, "DOMAIN": createDomainDictionary("one/two/three/four/five")},
        {"CODE": 200, "DOMAIN": createDomainDictionary("too000long000domain000name000with64letters000inside000kekekelolz")},
    ]

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        for rec in self.domainDictList:
            giverGive(rec["DOMAIN"]["ADDR"], TON * 2)
        
    # 2. Deploys
    def test_2(self):
        for rec in self.domainDictList:
            result = deployDomain(rec["DOMAIN"], 0, self.signer)
            self.assertEqual(result[1], rec["CODE"])

    # 3. Cleanup
    def test_3(self):
        for rec in self.domainDictList:
            result = callDomainFunction(domainDict=rec["DOMAIN"], functionName="TEST_selfdestruct", functionParams={}, signer=self.signer)
            self.assertEqual(result[1], 0)

# ==============================================================================
#
class Test_04_Prolongate(unittest.TestCase):
    
    signerD = generateSigner()
    signerM = generateSigner()
    domain  = createDomainDictionary("net")
    msig    = createMultisigDictionary(signerM.keys.public)

    # we know we have only 1 internal message, that's why this wrapper has no filters
    def _getExitCode(self, msgIdArray):
        abiArray     = [self.domain["ABI"], self.msig["ABI"]]
        msgArray     = unwrapMessages(msgIdArray, abiArray)
        realExitCode = msgArray[0]["TX_DETAILS"]["compute"]["exit_code"]
        return realExitCode        

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain["ADDR"], TON * 2)
        giverGive(self.msig  ["ADDR"], TON * 20)

    # 2. Deploy multisig
    def test_2(self):
        result = deployMultisig(self.msig, self.signerM)
        self.assertEqual(result[1], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = deployDomain(self.domain, "0x" + self.msig["ADDR"][2:], self.signerD)
        self.assertEqual(result[1], 0)

    # 4. Try prolongate
    def test_4(self):
        result = callDomainFunctionFromMultisig(domainDict=self.domain, msigDict=self.msig, functionName="prolongate", functionParams={}, value=100000000, flags=1, signer=self.signerM)
        self.assertEqual(result[1], 0) 

        # ERROR_CAN_NOT_PROLONGATE_YET is a result in internal message, can't see it here 
        # but can see in outgoing internal message result (it is MESSAGE ID with internal transaction): result[0].transaction["out_msgs"][0]
        # 
        realExitCode = self._getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 205) # ERROR_CAN_NOT_PROLONGATE_YET

        # HACK expiration date, set it 1 day from now
        result = callDomainFunctionFromMultisig(domainDict=self.domain, msigDict=self.msig, functionName="TEST_changeDtExpires", functionParams={"newDate":getNowTimestamp() + 60*60*24}, value=100000000, flags=1, signer=self.signerM)
        self.assertEqual(result[1], 0)

        # Try to prolongate again
        result = callDomainFunctionFromMultisig(domainDict=self.domain, msigDict=self.msig, functionName="prolongate", functionParams={}, value=100000000, flags=1, signer=self.signerM)
        self.assertEqual(result[1], 0)

        # Check again
        realExitCode = self._getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        # HACK expiration date, set it to be yesterday
        result = callDomainFunctionFromMultisig(domainDict=self.domain, msigDict=self.msig, functionName="TEST_changeDtExpires", functionParams={"newDate":getNowTimestamp() - 60*60*24}, value=100000000, flags=1, signer=self.signerM)
        self.assertEqual(result[1], 0)

        # Try to prolongate again
        result = callDomainFunctionFromMultisig(domainDict=self.domain, msigDict=self.msig, functionName="prolongate", functionParams={}, value=100000000, flags=1, signer=self.signerM)
        self.assertEqual(result[1], 0)

        # Check again
        realExitCode = self._getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 201) # ERROR_DOMAIN_IS_EXPIRED

    # 5. Cleanup
    def test_5(self):
        result = callDomainFunction(domainDict=self.domain, functionName="TEST_selfdestruct", functionParams={}, signer=self.signerD)
        self.assertEqual(result[1], 0)

# ==============================================================================
#
class Test_05_ClaimFFA(unittest.TestCase):
    
    signerD  = generateSigner()
    signerM1 = generateSigner()
    signerM2 = generateSigner()
    domain1  = createDomainDictionary("net")
    domain2  = createDomainDictionary("net/kek")
    msig1    = createMultisigDictionary(signerM1.keys.public)
    msig2    = createMultisigDictionary(signerM2.keys.public)

    # we know we have only 1 internal message, that's why this wrapper has no filters
    def _getExitCode(self, msgIdArray):
        abiArray     = [self.domain1["ABI"], self.msig1["ABI"]]
        msgArray     = unwrapMessages(msgIdArray, abiArray)
        realExitCode = msgArray[0]["TX_DETAILS"]["compute"]["exit_code"]
        return realExitCode        

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain1["ADDR"], TON * 2)
        giverGive(self.domain2["ADDR"], TON * 2)
        giverGive(self.msig1  ["ADDR"], TON * 20)
        giverGive(self.msig2  ["ADDR"], TON * 20)

    # 2. Deploy multisig
    def test_2(self):
        result = deployMultisig(self.msig1, self.signerM1)
        result = deployMultisig(self.msig2, self.signerM2)
        self.assertEqual(result[1], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = deployDomain(self.domain1, "0x" + self.msig1["ADDR"][2:], self.signerM1)
        self.assertEqual(result[1], 0)

    # 4. Deploy "net/kek"
    def test_4(self):
        result = deployDomain(self.domain2, "0x" + self.msig2["ADDR"][2:], self.signerM2)
        self.assertEqual(result[1], 0)

        result = runDomainFunction(domainDict=self.domain2, functionName="getOwnerID", functionParams={})
        self.assertEqual(result, "0x0000000000000000000000000000000000000000000000000000000000000000")

    # 5. Claim
    def test_5(self):
        result = callDomainFunctionFromMultisig(domainDict=self.domain1, msigDict=self.msig1, functionName="changeRegistrationType", functionParams={"newType":0}, value=100000000, flags=1, signer=self.signerM1)
        self.assertEqual(result[1], 0)
        
        realExitCode = self._getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        result = runDomainFunction(domainDict=self.domain2, functionName="getRegistrationType", functionParams={})
        self.assertEqual(result, "0")

        result = callDomainFunctionFromMultisig(domainDict=self.domain2, msigDict=self.msig2, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig2["ADDR"][2:],"tonsToInclude":100000000}, value=200000000, flags=1, signer=self.signerM2)
        self.assertEqual(result[1], 0)
        
        realExitCode = self._getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        result = runDomainFunction(domainDict=self.domain2, functionName="getOwnerID", functionParams={})
        self.assertEqual(result, "0x" + self.msig2["ADDR"][2:])

    # 5. Cleanup
    def test_6(self):
        result = callDomainFunction(domainDict=self.domain1, functionName="TEST_selfdestruct", functionParams={}, signer=self.signerD)
        self.assertEqual(result[1], 0)
        result = callDomainFunction(domainDict=self.domain2, functionName="TEST_selfdestruct", functionParams={}, signer=self.signerD)
        self.assertEqual(result[1], 0)

# ==============================================================================
# TODO
class Test_06_ClaimMoney(unittest.TestCase):       

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

# ==============================================================================
# TODO
class Test_07_ClaimOwner(unittest.TestCase):       

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

# ==============================================================================
# TODO
class Test_08_ClaimDeny(unittest.TestCase):       

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

# ==============================================================================
# TODO
class Test_09_RegisterWithNoParent(unittest.TestCase):       

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

# ==============================================================================
# TODO
class Test_10_CheckWhoisStatistics(unittest.TestCase):       

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

# ==============================================================================
# TODO
class Test_11_ChangeWhois(unittest.TestCase):       

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

# ==============================================================================
# TODO
class Test_12_ReleaseDomain(unittest.TestCase):       

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

# ==============================================================================
# TODO
class Test_11_WithdrawBalance(unittest.TestCase):       

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

# ==============================================================================
# 
unittest.main()

# ==============================================================================
# Decode custom BOC using ABI 
#
#boc = "te6ccgEBAQEAKAAAS2t6vFCADxflfdRZrf848WFZRhwB9MTzCbgDWgajIqAECjqEvjyQ"
#params = ParamsOfDecodeMessageBody(abi=getAbi("../bin/DnsRecordTEST.abi.json"), body=boc, is_internal=True)
#result = asyncClient.abi.decode_message_body(params=params)

#print(result.body_type, result.value, result.name, result.header)
#exit()