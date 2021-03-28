#!/usr/bin/env python3

# ==============================================================================
# 
from freeton_utils import *
import unittest

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
def deployDomain(domainDict, ownerAddress, ownerPubkey, keysFile):
    result = deployContract(abiPath=domainDict["ABI"], tvcPath=domainDict["TVC"], constructorInput={"ownerAddress":ownerAddress,"ownerPubkey":ownerPubkey}, initialData=domainDict["INIT"], signer=getSigner(keysFile), initialPubkey=ZERO_PUBKEY)
    return result

def callDomainFunction(domainDict, functionName, functionParams, keysFile):
    signer = getSigner(keysFile)
    result = callFunction(abiPath=domainDict["ABI"], contractAddress=domainDict["ADDR"], functionName=functionName, functionParams=functionParams, signer=signer)
    return result

def runDomainFunction(domainDict, functionName, functionParams):
    result = runFunction(abiPath=domainDict["ABI"], contractAddress=domainDict["ADDR"], functionName=functionName, functionParams=functionParams)
    return result

# ==============================================================================
# 
class DeployDomains(unittest.TestCase):

    domain1 = createDomainDictionary("org")
    domain2 = createDomainDictionary("test")
    domain3 = createDomainDictionary("defi")
    domain4 = createDomainDictionary("wrongLETTER")

    # Deploy first domain
    def test_deploy1(self):
        giverGive(self.domain1["ADDR"], 1000000000)
        result = deployDomain(self.domain1, "", ZERO_PUBKEY, "keys1.json")
        self.assertEqual(result[1], 0)

    # Deploy same one, should be ERROR 51
    def test_deploy2(self):
        result = deployDomain(self.domain1, "", ZERO_PUBKEY, "keys1.json")
        self.assertEqual(result[1], 51)

    def test_deploy3(self):
        giverGive(self.domain2["ADDR"], 1000000000)
        result = deployDomain(self.domain2, "", ZERO_PUBKEY, "keys1.json")
        self.assertEqual(result[1], 0)

    def test_deploy4(self):
        giverGive(self.domain3["ADDR"], 1000000000)
        result = deployDomain(self.domain3, "", ZERO_PUBKEY, "keys1.json")
        self.assertEqual(result[1], 0)

    def test_deploy5(self):
        giverGive(self.domain4["ADDR"], 1000000000)
        result = deployDomain(self.domain4, "", ZERO_PUBKEY, "keys1.json")
        self.assertEqual(result[1], 200)

    #========================================
    #
    def test_destroy1(self):
        result = callDomainFunction(self.domain1, "TEST_selfdestruct", {}, "keys1.json")
        self.assertEqual(result[1], 0)

    def test_destroy2(self):
        result = callDomainFunction(self.domain2, "TEST_selfdestruct", {}, "keys1.json")
        self.assertEqual(result[1], 0)

    def test_destroy3(self):
        result = callDomainFunction(self.domain3, "TEST_selfdestruct", {}, "keys1.json")
        self.assertEqual(result[1], 0)

    def test_destroy4(self):
        result = callDomainFunction(self.domain4, "TEST_selfdestruct", {}, "keys1.json")
        self.assertEqual(result[1], 0)



# ==============================================================================
# 
unittest.main()

#domain1 = createDomainDictionary("joshuah")

#print("============================================================")
#print("Address:", domain1["ADDR"  ])
#print("Name:   ", domain1["NAME"  ])
#print("Hex:    ", domain1["DOMAIN"])
#print("============================================================")

#giverGive(domain1["ADDR"], 1000000000)
#result = deployContract(abiPath=domain1["ABI"], tvcPath=domain1["TVC"], constructorInput={"ownerAddress":"","ownerPubkey":ZERO_PUBKEY}, initialData=domain1["INIT"], signer=getSigner("keys1.json"), initialPubkey=ZERO_PUBKEY)

#result = runFunction(abiPath=domain1["ABI"], contractAddress=domain1["ADDR"], functionName="getEndpointAddress", functionInputs={})
#print("getEndpointAddress:", result)