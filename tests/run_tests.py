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

for i, arg in enumerate(sys.argv[1:]):
    if arg == "--disable-giver":
        USE_GIVER = False
        sys.argv.remove(arg)
    elif arg.startswith("http"):
        CUSTOM_URL = arg
        sys.argv.remove(arg)

changeConfig(CUSTOM_URL, USE_GIVER)

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
        "ADDR":   getAddressZeroPubkey(ABI, TVC, INIT)
    }
    return domainDictionary

# ==============================================================================
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
# 
class Test_SameNameDeploy(unittest.TestCase):

    domain = createDomainDictionary("org")
    signer = generateSigner()
    
    def test_0(self):
        print("----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain["ADDR"], TON * 2)

    # 2. Deploy "org"
    def test_2(self):
        result = deployDomain(self.domain, 0, self.signer)
        self.assertEqual(result[1], 0)

    # 2. Deploy "org" once again
    def test_3(self):
        result = deployDomain(self.domain, 0, self.signer)
        self.assertEqual(result[1], 51)

    # 2. Cleanup
    def test_4(self):
        result = callDomainFunction(self.domain, "TEST_selfdestruct", {}, self.signer)
        self.assertEqual(result[1], 0)

# ==============================================================================
# 
unittest.main()

# ==============================================================================
# 
