#!/usr/bin/env python3

# ==============================================================================
# 
import freeton_utils
from   freeton_utils import *
import unittest
import time
import sys
from   pprint import pprint
from   contract_DnsRecord import DnsRecord

TON = 1000000000

# ==============================================================================
# 
# Parse arguments and then clear them because UnitTest will @#$~!
for _, arg in enumerate(sys.argv[1:]):
    if arg == "--disable-giver":
        
        freeton_utils.USE_GIVER = False
        sys.argv.remove(arg)

    if arg == "--throw":
        
        freeton_utils.THROW = True
        sys.argv.remove(arg)

    if arg.startswith("http"):
        
        freeton_utils.asyncClient = TonClient(config=ClientConfig(network=NetworkConfig(server_address=arg)))
        sys.argv.remove(arg)

    if arg.startswith("--msig-giver"):
        
        freeton_utils.MSIG_GIVER = arg[13:]
        sys.argv.remove(arg)

# ==============================================================================
# EXIT CODE FOR SINGLE-MESSAGE OPERATIONS
# we know we have only 1 internal message, that's why this wrapper has no filters
def _getAbiArray():
    return ["../bin/DnsRecordTEST.abi.json", "../bin/SetcodeMultisigWallet.abi.json"]

def _getExitCode(msgIdArray):
    abiArray     = _getAbiArray()
    msgArray     = unwrapMessages(msgIdArray, abiArray)
    if msgArray != "":
        realExitCode = msgArray[0]["TX_DETAILS"]["compute"]["exit_code"]
    else:
        realExitCode = -1
    return realExitCode   

# ==============================================================================
# 
class Test_01_SameNameDeploy(unittest.TestCase):

    #signer = generateSigner()
    domain = DnsRecord(name = "org")
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain.ADDRESS, TON * 1)

    # 2. Deploy "org"
    def test_2(self):
        result = self.domain.deploy(ownerID = "0x00")
        self.assertEqual(result[1]["errorCode"], 0)

    # 3. Deploy "org" once again
    def test_3(self):
        result = self.domain.deploy(ownerID = "0x00")
        self.assertEqual(result[1]["errorCode"], 51)

    # 4. Cleanup
    def test_4(self):
        result = self.domain.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
#
class Test_02_DeployWithMultisigOwner(unittest.TestCase):
    
    domain = DnsRecord(name = "net")
    msig   = Multisig()
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain.ADDRESS, TON * 1)
        giverGive(self.msig.ADDRESS,   TON * 1)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = self.domain.deploy(ownerID = "0x" + self.msig.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. Call change endpoint from multisig
    def test_4(self):
        endpoint = "0:78bf2beea2cd6ff9c78b0aca30e00fa627984dc01ad0351915002051d425f1e4"
        result = self.domain.callFromMultisig(msig=self.msig, functionName="changeEndpointAddress", functionParams={"newAddress":endpoint}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain.run(functionName="getEndpointAddress", functionParams={})
        self.assertEqual(result, endpoint)

    # 5. Cleanup
    def test_5(self):
        result = self.domain.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
#
class Test_03_WrongNames(unittest.TestCase):
    
    domainDictList = [
        {"CODE": 0,   "DOMAIN": DnsRecord(name = "org-org")},
        {"CODE": 200, "DOMAIN": DnsRecord(name = "ORG")},
        {"CODE": 200, "DOMAIN": DnsRecord(name = "F@!#ING")},
        {"CODE": 200, "DOMAIN": DnsRecord(name = "ddd//dd")},
        {"CODE": 200, "DOMAIN": DnsRecord(name = "//")},
        {"CODE": 200, "DOMAIN": DnsRecord(name = "")},
        {"CODE": 200, "DOMAIN": DnsRecord(name = "under_score")},
        {"CODE": 0,   "DOMAIN": DnsRecord(name = "good-domain-name-with-31-letter")},
        {"CODE": 200, "DOMAIN": DnsRecord(name = "perfectly000fine000domain000name000with63letters000inside000kek")},
        {"CODE": 0,   "DOMAIN": DnsRecord(name = "one/two/three/four")},
        {"CODE": 200, "DOMAIN": DnsRecord(name = "one/two/three/four/five")},
        {"CODE": 200, "DOMAIN": DnsRecord(name = "too000long000domain000name000with64letters000inside000kekekelolz")},
    ]

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        for rec in self.domainDictList:
            giverGive(rec["DOMAIN"].ADDRESS, TON * 1)
        
    # 2. Deploys
    def test_2(self):
        for rec in self.domainDictList:
            result = rec["DOMAIN"].deploy(ownerID = "0x00")
            self.assertEqual(result[1]["errorCode"], rec["CODE"])

    # 3. Cleanup
    def test_3(self):
        for rec in self.domainDictList:
            result = rec["DOMAIN"].destroy(addressDest = freeton_utils.giverGetAddress())
            self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
#
class Test_04_Prolongate(unittest.TestCase):
    
    domain = DnsRecord(name = "net")
    msig   = Multisig()


    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain.ADDRESS, TON * 1)
        giverGive(self.msig.ADDRESS,   TON * 1)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = self.domain.deploy(ownerID = "0x" + self.msig.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. Try prolongate
    def test_4(self):
        result = self.domain.callFromMultisig(msig=self.msig, functionName="prolongate", functionParams={}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0) 

        # ERROR_CAN_NOT_PROLONGATE_YET is a result in internal message, can't see it here 
        # but can see in outgoing internal message result (it is MESSAGE ID with internal transaction): result[0].transaction["out_msgs"][0]
        # 
        realExitCode = _getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 205) # ERROR_CAN_NOT_PROLONGATE_YET

        # HACK expiration date, set it 1 day from now

        result = self.domain.callFromMultisig(msig=self.msig, functionName="TEST_changeDtExpires", functionParams={"newDate":getNowTimestamp() + 60*60*24}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        # Try to prolongate again
        result = self.domain.callFromMultisig(msig=self.msig, functionName="prolongate", functionParams={}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        # Check again
        realExitCode = _getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        # HACK expiration date, set it to be yesterday
        result = self.domain.callFromMultisig(msig=self.msig, functionName="TEST_changeDtExpires", functionParams={"newDate":getNowTimestamp() - 60*60*24}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        # Try to prolongate again
        result = self.domain.callFromMultisig(msig=self.msig, functionName="prolongate", functionParams={}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        # Check again
        realExitCode = _getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 201) # ERROR_DOMAIN_IS_EXPIRED

    # 5. Cleanup
    def test_5(self):
        result = self.domain.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
#
class Test_05_ClaimFFA(unittest.TestCase):
    
    domain_net     = DnsRecord(name="net")
    domain_net_kek = DnsRecord(name="net/kek")
    msig1          = Multisig()
    msig2          = Multisig()

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain_net.ADDRESS,     TON * 1)
        giverGive(self.domain_net_kek.ADDRESS, TON * 1)
        giverGive(self.msig1.ADDRESS,          TON * 1)
        giverGive(self.msig2.ADDRESS,          TON * 1)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = self.domain_net.deploy(ownerID = "0x" + self.msig1.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. Deploy "net/kek"
    def test_4(self):
        result = self.domain_net_kek.deploy(ownerID = "0x" + self.msig2.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain_net_kek.run(functionName="getOwnerID", functionParams={})
        self.assertEqual(result, "0x0000000000000000000000000000000000000000000000000000000000000000")

    # 5. Claim
    def test_5(self):

        result = self.domain_net.callFromMultisig(msig=self.msig1, functionName="changeRegistrationType", functionParams={"newType":0}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        
        realExitCode = _getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        result = self.domain_net.run(functionName="getRegistrationType", functionParams={})
        self.assertEqual(result, "0")

        result = self.domain_net_kek.callFromMultisig(msig=self.msig2, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain_net_kek.run(functionName="getOwnerID", functionParams={})
        self.assertEqual(result, "0x" + self.msig2.ADDRESS[2:])

    # 6. Cleanup
    def test_6(self):
        result = self.domain_net.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_net_kek.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.msig1.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
# 
class Test_06_ClaimMoney(unittest.TestCase):

    domain_domaino     = DnsRecord(name="domaino")
    domain_domaino_kek = DnsRecord(name="domaino/kek")
    msig1              = Multisig()
    msig2              = Multisig()
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain_domaino.ADDRESS,     TON * 1)
        giverGive(self.domain_domaino_kek.ADDRESS, TON * 1)
        giverGive(self.msig1.ADDRESS,              TON * 1)
        giverGive(self.msig2.ADDRESS,              TON * 1)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "domaino" and "domaino/kek"
    def test_3(self):
        result = self.domain_domaino.deploy(ownerID = "0x" + self.msig1.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino_kek.deploy(ownerID = "0x" + ZERO_PUBKEY)
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. change Whois and get Whois
    def test_4(self):
        regPrice = 200000000

        # Set registration type to MONEY
        result = self.domain_domaino.callFromMultisig(msig=self.msig1, functionName="changeRegistrationType", functionParams={"newType":1}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain_domaino.callFromMultisig(msig=self.msig1, functionName="changeSubdomainRegPrice", functionParams={"price":regPrice}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        #
        result = getAccountGraphQL(self.domain_domaino.ADDRESS, "balance(format:DEC)")
        balanceBefore = int(result["balance"])

        # Claim
        result = self.domain_domaino_kek.callFromMultisig(msig=self.msig1, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=400000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        # Get "storage_fees" into account
        msgArray = unwrapMessages(result[0].transaction["out_msgs"], _getAbiArray())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "receiveRegistrationRequest":
                balanceBefore -= int(msg["TX_DETAILS"]["storage"]["storage_fees_collected"])

        # Check new parent balance
        result = getAccountGraphQL(self.domain_domaino.ADDRESS, "balance(format:DEC)")
        balanceAfter = int(result["balance"])
        self.assertEqual(balanceAfter, balanceBefore + regPrice)

        # Check correct owner
        result = self.domain_domaino_kek.run(functionName="getWhois", functionParams={})
        self.assertEqual(result["ownerID"], "0x" + self.msig2.ADDRESS[2:])

    # 5. Cleanup
    def test_5(self):
        result = self.domain_domaino.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino_kek.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.msig1.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
# 
class Test_07_ClaimOwner(unittest.TestCase):

    domain_domaino     = DnsRecord(name="domaino")
    domain_domaino_kek = DnsRecord(name="domaino/kek")
    msig1              = Multisig()
    msig2              = Multisig()
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain_domaino.ADDRESS,     TON * 1)
        giverGive(self.domain_domaino_kek.ADDRESS, TON * 1)
        giverGive(self.msig1.ADDRESS,              TON * 1)
        giverGive(self.msig2.ADDRESS,              TON * 1)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "domaino" and "domaino/kek"
    def test_3(self):
        result = self.domain_domaino.deploy(ownerID = "0x" + self.msig1.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino_kek.deploy(ownerID = "0x" + ZERO_PUBKEY)
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. Try to claim the domain
    def test_4(self):

        # Set registration type to OWNER
        result = self.domain_domaino.callFromMultisig(msig=self.msig1, functionName="changeRegistrationType", functionParams={"newType":2}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        # Claim witn msig2 owner (wrong)
        result = self.domain_domaino_kek.callFromMultisig(msig=self.msig2, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        msgArray = unwrapMessages(result[0].transaction["out_msgs"], _getAbiArray())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                self.assertEqual(msg["FUNCTION_PARAMS"]["result"], "2") # DENIED

        # Claim with right owner
        result = self.domain_domaino_kek.callFromMultisig(msig=self.msig2, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig1.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        
        msgArray = unwrapMessages(result[0].transaction["out_msgs"], _getAbiArray())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                self.assertEqual(msg["FUNCTION_PARAMS"]["result"], "1") # APPROVED

        # Check correct owner
        result = self.domain_domaino_kek.run(functionName="getWhois", functionParams={})
        self.assertEqual(result["ownerID"], "0x" + self.msig1.ADDRESS[2:])

    # 5. Cleanup
    def test_5(self):
        result = self.domain_domaino.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino_kek.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.msig1.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
# 
class Test_08_ClaimDeny(unittest.TestCase):       

    domain_net     = DnsRecord(name="net")
    domain_net_kek = DnsRecord(name="net/kek")
    msig1          = Multisig()
    msig2          = Multisig()

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain_net.ADDRESS,     TON * 1)
        giverGive(self.domain_net_kek.ADDRESS, TON * 1)
        giverGive(self.msig1.ADDRESS,          TON * 1)
        giverGive(self.msig2.ADDRESS,          TON * 1)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = self.domain_net.deploy(ownerID = "0x" + self.msig1.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. Deploy "net/kek"
    def test_4(self):
        result = self.domain_net_kek.deploy(ownerID = "0x" + ZERO_PUBKEY)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain_net_kek.run(functionName="getOwnerID", functionParams={})
        self.assertEqual(result, "0x0000000000000000000000000000000000000000000000000000000000000000")

    # 5. Claim
    def test_5(self):
        result = self.domain_net.callFromMultisig(msig=self.msig1, functionName="changeRegistrationType", functionParams={"newType":3}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        
        realExitCode = _getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        result = self.domain_net.run(functionName="getRegistrationType", functionParams={})
        self.assertEqual(result, "3")

        result = self.domain_net_kek.callFromMultisig(msig=self.msig2, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        
        # Check registration result
        msgArray = unwrapMessages(result[0].transaction["out_msgs"], _getAbiArray())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                regResult = msg["FUNCTION_PARAMS"]["result"]
                self.assertEqual(regResult, "2") # DENIED
        
        result = self.domain_net_kek.run(functionName="getOwnerID", functionParams={})
        self.assertEqual(result, "0x" + ZERO_PUBKEY)

    # 6. Cleanup
    def test_6(self):
        result = self.domain_net.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_net_kek.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.msig1.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
# 
class Test_09_RegisterWithNoParent(unittest.TestCase):

    domain = DnsRecord(name="net/some/shit")
    msig   = Multisig()

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain.ADDRESS, TON * 1)
        giverGive(self.msig.ADDRESS,   TON * 1)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "net/some/shit"
    def test_3(self):
        result = self.domain.deploy(ownerID = "0x" + ZERO_PUBKEY)
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. Claim
    def test_4(self):
        result = self.domain.callFromMultisig(msig=self.msig, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        
        # Check onBounce/aborted
        msgArray = unwrapMessages(result[0].transaction["out_msgs"], _getAbiArray())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "receiveRegistrationRequest":
                regResult = msg["TX_DETAILS"]["aborted"]
                self.assertEqual(regResult, True) # Aborted

        # Owner should still be 0
        result = self.domain.run(functionName="getOwnerID", functionParams={})
        self.assertEqual(result, "0x" + ZERO_PUBKEY)

    # 5. Cleanup
    def test_5(self):
        result = self.domain.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
# 
class Test_10_CheckWhoisStatistics(unittest.TestCase):       

    domain_domaino     = DnsRecord(name="domaino")
    domain_domaino_kek = DnsRecord(name="domaino/kek")
    msig1              = Multisig()
    msig2              = Multisig()
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain_domaino.ADDRESS,     TON * 1)
        giverGive(self.domain_domaino_kek.ADDRESS, TON * 1)
        giverGive(self.msig1.ADDRESS,              TON * 1)
        giverGive(self.msig2.ADDRESS,              TON * 1)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "domaino" and "domaino/kek"
    def test_3(self):
        result = self.domain_domaino.deploy(ownerID = "0x" + self.msig1.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino_kek.deploy(ownerID = "0x" + ZERO_PUBKEY)
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. change Whois and get Whois
    def test_4(self):
        price = 200000000

        # Change owners 6 times
        result = self.domain_domaino.callFromMultisig(msig=self.msig1, functionName="changeOwner", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino.callFromMultisig(msig=self.msig2, functionName="changeOwner", functionParams={"newOwnerID":"0x" + self.msig1.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino.callFromMultisig(msig=self.msig1, functionName="changeOwner", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino.callFromMultisig(msig=self.msig2, functionName="changeOwner", functionParams={"newOwnerID":"0x" + self.msig1.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino.callFromMultisig(msig=self.msig1, functionName="changeOwner", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino.callFromMultisig(msig=self.msig2, functionName="changeOwner", functionParams={"newOwnerID":"0x" + self.msig1.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain_domaino.run(functionName="getWhois", functionParams={})
        self.assertEqual(result["totalOwnersNum"], "7")

        # Deny subdomain registration 
        result = self.domain_domaino.callFromMultisig(msig=self.msig1, functionName="changeRegistrationType", functionParams={"newType":3}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain_domaino_kek.callFromMultisig(msig=self.msig1, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        
        # Check registration result
        msgArray = unwrapMessages(result[0].transaction["out_msgs"], _getAbiArray())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                regResult = msg["FUNCTION_PARAMS"]["result"]
                self.assertEqual(regResult, "2") # DENIED

        result = self.domain_domaino.run(functionName="getWhois", functionParams={})
        self.assertEqual(result["subdomainRegDenied"], "1")

        # Money registration covers two stats: "subdomainRegAccepted" and "totalFeesCollected"
        result = self.domain_domaino.callFromMultisig(msig=self.msig1, functionName="changeRegistrationType", functionParams={"newType":1}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain_domaino.callFromMultisig(msig=self.msig1, functionName="changeSubdomainRegPrice", functionParams={"price":price}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        # We try to include less money than price
        result = self.domain_domaino_kek.callFromMultisig(msig=self.msig1, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        
        msgArray = unwrapMessages(result[0].transaction["out_msgs"], _getAbiArray())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                regResult = msg["FUNCTION_PARAMS"]["result"]
                self.assertEqual(regResult, "3") # NOT_ENOUGH_MONEY

        # Claim
        result = self.domain_domaino_kek.callFromMultisig(msig=self.msig1, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=400000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain_domaino.run(functionName="getWhois", functionParams={})
        self.assertEqual(result["subdomainRegAccepted"], "1"       )
        self.assertEqual(result["totalFeesCollected"],   str(price))

        # Check correct owner
        result = self.domain_domaino_kek.run(functionName="getWhois", functionParams={})
        self.assertEqual(result["ownerID"], "0x" + self.msig2.ADDRESS[2:])

    # 5. Cleanup
    def test_5(self):
        result = self.domain_domaino.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain_domaino_kek.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.msig1.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
# 
class Test_11_ChangeWhois(unittest.TestCase):   
    
    domain = DnsRecord(name="domaino")
    msig   = Multisig()
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain.ADDRESS, TON * 1)
        giverGive(self.msig.ADDRESS,   TON * 1)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "domaino"
    def test_3(self):
        result = self.domain.deploy(ownerID = "0x" + self.msig.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. change Whois and get Whois
    def test_4(self):
        endpointAddress = self.msig.ADDRESS
        comment         = stringToHex("wassup you boyz!!!@@#%")
        
        result = self.domain.callFromMultisig(msig=self.msig, functionName="changeEndpointAddress", functionParams={"newAddress":endpointAddress}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.domain.callFromMultisig(msig=self.msig, functionName="changeComment", functionParams={"newComment":comment}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain.run(functionName="getWhois", functionParams={})
        self.assertEqual(result["endpointAddress"], endpointAddress)
        self.assertEqual(result["comment"],         comment        )

    # 5. Cleanup
    def test_5(self):
        result = self.domain.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.msig.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
# 
class Test_12_ReleaseDomain(unittest.TestCase): 
    
    domain = DnsRecord(name="dominos")
    msig   = Multisig()
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain.ADDRESS, TON * 1)
        giverGive(self.msig.ADDRESS,   TON * 1)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "dominos"
    def test_3(self):
        result = self.domain.deploy(ownerID = "0x" + self.msig.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. change Whois and get Whois
    def test_4(self):
        result = self.domain.callFromMultisig(msig=self.msig, functionName="releaseDomain", functionParams={}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.domain.run(functionName="getWhois", functionParams={})
        self.assertEqual(result["ownerID"],          "0x" + ZERO_PUBKEY)
        self.assertEqual(result["dtExpires"],        "0"               )
        self.assertEqual(result["endpointAddress"],  ZERO_ADDRESS      )
        self.assertEqual(result["registrationType"], "3"               )
        self.assertEqual(result["comment"],          ""                )

    # 5. Cleanup
    def test_5(self):
        result = self.domain.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.msig.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)


# ==============================================================================
# 
class Test_13_WithdrawBalance(unittest.TestCase):
    
    domain = DnsRecord(name="dominos")
    msig   = Multisig()
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain.ADDRESS, TON * 1)
        giverGive(self.msig.ADDRESS,   TON * 1)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "dominos"
    def test_3(self):
        result = self.domain.deploy(ownerID = "0x" + self.msig.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. Withdraw some TONs
    def test_4(self):
        amount = 200000000

        # Get balances
        result = getAccountGraphQL(self.domain.ADDRESS, "balance(format:DEC)")
        balanceDomain1 = int(result["balance"])
        
        result = getAccountGraphQL(self.msig.ADDRESS, "balance(format:DEC)")
        balanceMsig1 = int(result["balance"])
        
        # Withdraw
        result = self.domain.callFromMultisig(msig=self.msig, functionName="withdrawBalance", functionParams={"amount":amount,"dest":self.msig.ADDRESS}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        # Get balances again
        result = getAccountGraphQL(self.domain.ADDRESS, "balance(format:DEC)")
        balanceDomain2 = int(result["balance"])

        result = getAccountGraphQL(self.msig.ADDRESS, "balance(format:DEC)")
        balanceMsig2 = int(result["balance"])

        # I DON'T KNOW HOW TO CALCULATE EXACT BALANCE! sigh
        self.assertLess   (balanceDomain2, balanceDomain1 - amount)
        self.assertLess   (balanceMsig2,   balanceMsig1   + amount)
        self.assertGreater(balanceMsig2,   balanceMsig1)

    # 5. Cleanup
    def test_5(self):
        result = self.domain.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.msig.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
# 
class Test_14_ClaimAlreadyClaimed(unittest.TestCase):       

    domain = DnsRecord(name="domaino")
    msig1  = Multisig()
    msig2  = Multisig()
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(self.domain.ADDRESS, TON * 1)
        giverGive(self.msig1.ADDRESS,  TON * 1)
        giverGive(self.msig2.ADDRESS,  TON * 1)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result[1]["errorCode"], 0)
        
    # 3. Deploy "domaino"
    def test_3(self):
        result = self.domain.deploy(ownerID = "0x" + self.msig1.ADDRESS[2:])
        self.assertEqual(result[1]["errorCode"], 0)

    # 4. Try to claim
    def test_4(self):
        # Change to FFA
        result = self.domain.callFromMultisig(msig=self.msig1, functionName="changeRegistrationType", functionParams={"newType":0}, value=100000000, flags=1)
        self.assertEqual(result[1]["errorCode"], 0)

        # Try to claim from other multisig
        result = self.domain.callFromMultisig(msig=self.msig2, functionName="claimExpired", functionParams={"newOwnerID":"0x" + self.msig2.ADDRESS[2:]}, value=100000000, flags=1)
        realExitCode = _getExitCode(msgIdArray=result[0].transaction["out_msgs"])
        self.assertEqual(realExitCode, 202) # ERROR_DOMAIN_IS_NOT_EXPIRED

    # 5. Cleanup
    def test_5(self):
        result = self.domain.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

        result = self.msig1.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)
        result = self.msig2.destroy(addressDest = freeton_utils.giverGetAddress())
        self.assertEqual(result[1]["errorCode"], 0)

# ==============================================================================
# 
unittest.main()
