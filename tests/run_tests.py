#!/usr/bin/env python3

# ==============================================================================
# 
import ever_utils
from   ever_utils import *
import unittest
import time
import sys
from   pprint import pprint
from   contract_DnsRecord         import DnsRecord
from   contract_DnsRecordTEST     import DnsRecordTEST
from   contract_DnsDebotTEST      import DnsDebotTEST
from   contract_DnsDebot          import DnsDebot

# ==============================================================================
#
SERVER_ADDRESS = "https://net.ton.dev"

# ==============================================================================
#
def getClient():
    return getEverClient(testnet=False, customServer=SERVER_ADDRESS)

# ==============================================================================
# 
# Parse arguments and then clear them because UnitTest will @#$~!
for _, arg in enumerate(sys.argv[1:]):
    if arg == "--disable-giver":
        
        ever_utils.USE_GIVER = False
        sys.argv.remove(arg)

    if arg == "--throw":
        
        ever_utils.THROW = True
        sys.argv.remove(arg)

    if arg.startswith("http"):
        
        SERVER_ADDRESS = arg
        sys.argv.remove(arg)

    if arg.startswith("--msig-giver"):
        
        ever_utils.MSIG_GIVER = arg[13:]
        sys.argv.remove(arg)

# ==============================================================================
# EXIT CODE FOR SINGLE-MESSAGE OPERATIONS
# we know we have only 1 internal message, that's why this wrapper has no filters
"""
def _getAbiArray():
    return ["../bin/DnsRecordTEST.abi.json", "../bin/SetcodeMultisigWallet.abi.json", "../bin/DnsDebotTEST.abi.json", "../bin/DnsRecordDeployer.abi.json"]

def _getExitCode(msgIdArray):
    abiArray     = _getAbiArray()
    msgArray     = unwrapMessages(getClient(), msgIdArray, abiArray)
    if msgArray != "":
        realExitCode = msgArray[0]["TX_DETAILS"]["compute"]["exit_code"]
    else:
        realExitCode = -1
    return realExitCode   
"""
# ==============================================================================
# 
class Test_01_SameNameDeploy(unittest.TestCase):

    msig   = Multisig(everClient=getClient())
    domain = DnsRecordTEST(everClient=getClient(), name="org", ownerAddress=msig.ADDRESS)
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain.ADDRESS, EVER * 1)
        giverGive(getClient(), self.msig.ADDRESS,   EVER * 1)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 3. Deploy "org"
    def test_3(self):
        result = self.domain.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. Deploy "org" once again
    def test_4(self):
        result = self.domain.deploy()
        self.assertEqual(result["exception"]["errorCode"], 51)

    # 5. Cleanup
    def test_5(self):
        result = self.domain.TEST_selfdestruct(msig=self.msig, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
#
class Test_02_DeployWithMultisigOwner(unittest.TestCase):
    
    msig   = Multisig(everClient=getClient())
    domain = DnsRecordTEST(everClient=getClient(), name="net", ownerAddress=msig.ADDRESS)
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain.ADDRESS, EVER * 1)
        giverGive(getClient(), self.msig.ADDRESS,   EVER * 1)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = self.domain.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. Call change endpoint from multisig
    def test_4(self):
        endpoint = "0:78bf2beea2cd6ff9c78b0aca30e00fa627984dc01ad0351915002051d425f1e4"
        result = self.domain.changeEndpointAddress(msig=self.msig, newAddress=endpoint)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain.getWhois()["endpointAddress"]
        self.assertEqual(result, endpoint)

    # 5. Cleanup
    def test_5(self):
        result = self.domain.TEST_selfdestruct(msig=self.msig, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
#
class Test_03_WrongNames(unittest.TestCase):
    
    msig = Multisig(everClient=getClient())
    domainDictList = [
        {"CODE": 0,   "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "org-org",                                                          ownerAddress=msig.ADDRESS)},
        {"CODE": 200, "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "ORG",                                                              ownerAddress=msig.ADDRESS)},
        {"CODE": 200, "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "F@!#ING",                                                          ownerAddress=msig.ADDRESS)},
        {"CODE": 200, "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "ddd//dd",                                                          ownerAddress=msig.ADDRESS)},
        {"CODE": 0,   "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "ff/ff",                                                            ownerAddress=msig.ADDRESS)},
        {"CODE": 200, "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "//",                                                               ownerAddress=msig.ADDRESS)},
        {"CODE": 200, "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "",                                                                 ownerAddress=msig.ADDRESS)},
        {"CODE": 200, "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "under_score",                                                      ownerAddress=msig.ADDRESS)},
        {"CODE": 0,   "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "good-domain-name-with-31-letter",                                  ownerAddress=msig.ADDRESS)},
        {"CODE": 200, "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "perfectly000fine000domain000name000with63letters000inside000kek",  ownerAddress=msig.ADDRESS)},
        {"CODE": 0,   "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "one/two/three/four",                                               ownerAddress=msig.ADDRESS)},
        {"CODE": 200, "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "one/two/three/four/five",                                          ownerAddress=msig.ADDRESS)},
        {"CODE": 200, "DOMAIN": DnsRecordTEST(everClient=getClient(), name = "too000long000domain000name000with64letters000inside000kekekelolz", ownerAddress=msig.ADDRESS)},
    ]


    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        for rec in self.domainDictList:
            giverGive(getClient(), rec["DOMAIN"].ADDRESS, EVER * 1)
        giverGive(getClient(), self.msig.ADDRESS, EVER * 1)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploys
    def test_3(self):
        for rec in self.domainDictList:
            result = rec["DOMAIN"].deploy()
            #self.assertEqual(result["exception"]["errorCode"], rec["CODE"])

    # 4. Cleanup
    def test_4(self):
        result = self.msig.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

        for rec in self.domainDictList:
            result = rec["DOMAIN"].TEST_selfdestruct(msig=self.msig, dest=ever_utils.giverGetAddress())
            self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
#
class Test_04_Prolongate(unittest.TestCase):
    
    msig   = Multisig(everClient=getClient())
    domain = DnsRecordTEST(everClient=getClient(), name="net", ownerAddress=msig.ADDRESS)

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig.ADDRESS,   EVER * 2)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = self.domain.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. Try prolongate
    def test_4(self):
        result = self.domain.prolongate(msig=self.msig)
        self.assertEqual(result["exception"]["errorCode"], 0) 

        # ERROR_CAN_NOT_PROLONGATE_YET is a result in internal message, can't see it here 
        # but can see in outgoing internal message result (it is MESSAGE ID with internal transaction): result[0].transaction["out_msgs"][0]
        # 
        #msgArray = unwrapMessages(result[0].transaction["out_msgs"], _getAbiArray())
        #pprint(msgArray)
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 205) # ERROR_CAN_NOT_PROLONGATE_YET

        # HACK expiration date, set it 1 day from now

        result = self.domain.TEST_changeDtExpires(msig=self.msig, newDate=getNowTimestamp() + 60*60*24)
        self.assertEqual(result["exception"]["errorCode"], 0)

        # Try to prolongate again
        result = self.domain.prolongate(msig=self.msig)
        self.assertEqual(result["exception"]["errorCode"], 0)

        # Check again
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        # HACK expiration date, set it to be yesterday
        result = self.domain.TEST_changeDtExpires(msig=self.msig, newDate=getNowTimestamp() - 60*60*24)
        self.assertEqual(result["exception"]["errorCode"], 0)

        # Try to prolongate again
        result = self.domain.prolongate(msig=self.msig)
        self.assertEqual(result["exception"]["errorCode"], 0)

        # Check again
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 201) # ERROR_DOMAIN_IS_EXPIRED

    # 5. Cleanup
    def test_5(self):
        result = self.domain.TEST_selfdestruct(msig=self.msig, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
#
class Test_05_ClaimFFA(unittest.TestCase):
    
    msig1          = Multisig(everClient=getClient())
    msig2          = Multisig(everClient=getClient())
    domain_net     = DnsRecordTEST(everClient=getClient(), name="net",     ownerAddress=msig1.ADDRESS)
    domain_net_kek = DnsRecordTEST(everClient=getClient(), name="net/kek", ownerAddress=msig2.ADDRESS)

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain_net.ADDRESS,     EVER * 2)
        giverGive(getClient(), self.domain_net_kek.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig1.ADDRESS,          EVER * 2)
        giverGive(getClient(), self.msig2.ADDRESS,          EVER * 2)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = self.domain_net.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. Deploy "net/kek"
    def test_4(self):
        result = self.domain_net_kek.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain_net_kek.getWhois()
        self.assertEqual(result["ownerAddress"], "0:0000000000000000000000000000000000000000000000000000000000000000")

    # 5. Claim
    def test_5(self):

        result       = self.domain_net.changeRegistrationType(msig=self.msig1, newType=0)
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        result = self.domain_net.getWhois()
        self.assertEqual(result["registrationType"], "0")

        result = self.domain_net_kek.claimExpired(msig=self.msig2, newOwnerAddress=self.msig2.ADDRESS)
        result = self.domain_net_kek.getWhois()
        self.assertEqual(result["ownerAddress"], self.msig2.ADDRESS)

    # 6. Cleanup
    def test_6(self):
        result = self.domain_net.TEST_selfdestruct(msig=self.msig1, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_net_kek.TEST_selfdestruct(msig=self.msig2, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.msig1.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
# 
class Test_06_ClaimMoney(unittest.TestCase):

    msig1              = Multisig(everClient=getClient())
    msig2              = Multisig(everClient=getClient())
    domain_domaino     = DnsRecordTEST(everClient=getClient(), name="domaino",     ownerAddress=msig1.ADDRESS)
    domain_domaino_kek = DnsRecordTEST(everClient=getClient(), name="domaino/kek", ownerAddress=msig2.ADDRESS)
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain_domaino.ADDRESS,     EVER * 2)
        giverGive(getClient(), self.domain_domaino_kek.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig1.ADDRESS,              EVER * 2)
        giverGive(getClient(), self.msig2.ADDRESS,              EVER * 2)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "domaino" and "domaino/kek"
    def test_3(self):
        result = self.domain_domaino.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino_kek.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. change Whois and get Whois
    def test_4(self):
        regPrice = DIME*2

        # Set registration type to MONEY
        result = self.domain_domaino.changeRegistrationType(msig=self.msig1, newType=1)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain_domaino.changeRegistrationPrice(msig=self.msig1, newPrice=regPrice)
        self.assertEqual(result["exception"]["errorCode"], 0)

        #
        balanceBefore = self.msig1.getBalance()

        # Claim
        result = self.domain_domaino_kek.claimExpired(msig=self.msig2, newOwnerAddress=self.msig2.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)

        # Include all the fees into calculation (when multisig receives transfer it pays fees too)
        msgArray = unwrapMessages(result=result, everClient=getClient())
        #pprint(msgArray)
        for msg in msgArray:
            if msg["DEST"] == self.msig1.ADDRESS:
                balanceBefore -= int(msg["TX_DETAILS"]["total_fees"])

        # Check new parent balance
        balanceAfter = self.msig1.getBalance()
        self.assertEqual(balanceAfter, balanceBefore + regPrice)

        # Check correct owner
        result = self.domain_domaino_kek.getWhois()
        self.assertEqual(result["ownerAddress"], self.msig2.ADDRESS)

    # 5. Cleanup
    def test_5(self):
        result = self.domain_domaino.TEST_selfdestruct(msig=self.msig1, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino_kek.TEST_selfdestruct(msig=self.msig2, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.msig1.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
# 
class Test_07_ClaimOwner(unittest.TestCase):

    msig1              = Multisig(everClient=getClient())
    msig2              = Multisig(everClient=getClient())
    domain_domaino     = DnsRecordTEST(everClient=getClient(), name="domaino",     ownerAddress=msig1.ADDRESS)
    domain_domaino_kek = DnsRecordTEST(everClient=getClient(), name="domaino/kek", ownerAddress=msig2.ADDRESS)
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain_domaino.ADDRESS,     EVER * 2)
        giverGive(getClient(), self.domain_domaino_kek.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig1.ADDRESS,              EVER * 2)
        giverGive(getClient(), self.msig2.ADDRESS,              EVER * 2)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "domaino" and "domaino/kek"
    def test_3(self):
        result = self.domain_domaino.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino_kek.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. Try to claim the domain
    def test_4(self):

        # Set registration type to OWNER
        result = self.domain_domaino.changeRegistrationType(msig=self.msig1, newType=2)
        self.assertEqual(result["exception"]["errorCode"], 0)

        # Claim witn msig2 owner (wrong)
        result = self.domain_domaino_kek.claimExpired(msig=self.msig2, newOwnerAddress=self.msig2.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)

        msgArray = unwrapMessages(result=result, everClient=getClient())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                self.assertEqual(msg["FUNCTION_PARAMS"]["result"], "2") # DENIED

        # Claim with right owner
        result = self.domain_domaino_kek.claimExpired(msig=self.msig2, newOwnerAddress=self.msig1.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)
        
        msgArray = unwrapMessages(result=result, everClient=getClient())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                self.assertEqual(msg["FUNCTION_PARAMS"]["result"], "1") # APPROVED

        # Check correct owner
        result = self.domain_domaino_kek.getWhois()
        self.assertEqual(result["ownerAddress"], self.msig1.ADDRESS)

    # 5. Cleanup
    def test_5(self):
        result = self.domain_domaino.TEST_selfdestruct(msig=self.msig1, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino_kek.TEST_selfdestruct(msig=self.msig2, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.msig1.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
# 
class Test_08_ClaimDeny(unittest.TestCase):       

    msig1          = Multisig(everClient=getClient())
    msig2          = Multisig(everClient=getClient())
    domain_net     = DnsRecordTEST(everClient=getClient(), name="net",     ownerAddress=msig1.ADDRESS)
    domain_net_kek = DnsRecordTEST(everClient=getClient(), name="net/kek", ownerAddress=msig2.ADDRESS)

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain_net.ADDRESS,     EVER * 2)
        giverGive(getClient(), self.domain_net_kek.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig1.ADDRESS,          EVER * 2)
        giverGive(getClient(), self.msig2.ADDRESS,          EVER * 2)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "net"
    def test_3(self):
        result = self.domain_net.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. Deploy "net/kek"
    def test_4(self):
        result = self.domain_net_kek.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain_net_kek.getWhois()
        self.assertEqual(result["ownerAddress"], ZERO_ADDRESS)

    # 5. Claim
    def test_5(self):
        result = self.domain_net.changeRegistrationType(msig=self.msig1, newType=3)
        self.assertEqual(result["exception"]["errorCode"], 0)
        
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        result = self.domain_net.getWhois()
        self.assertEqual(result["registrationType"], "3")

        result = self.domain_net_kek.claimExpired(msig=self.msig2, newOwnerAddress=self.msig2.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)
        
        # Check registration result
        msgArray = unwrapMessages(result=result, everClient=getClient())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                regResult = msg["FUNCTION_PARAMS"]["result"]
                self.assertEqual(regResult, "2") # DENIED
        
        result = self.domain_net_kek.getWhois()
        self.assertEqual(result["ownerAddress"], ZERO_ADDRESS)

    # 6. Cleanup
    def test_6(self):
        result = self.domain_net.TEST_selfdestruct(msig=self.msig1, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_net_kek.TEST_selfdestruct(msig=self.msig2, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.msig1.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
# 
class Test_09_RegisterWithNoParent(unittest.TestCase):

    msig   = Multisig(everClient=getClient())
    domain = DnsRecordTEST(everClient=getClient(), name="net/some/shit", ownerAddress=msig.ADDRESS)

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig.ADDRESS,   EVER * 2)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "net/some/shit"
    def test_3(self):
        result = self.domain.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. Claim
    def test_4(self):
        result = self.domain.claimExpired(msig=self.msig, newOwnerAddress=self.msig.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)
        
        # Check onBounce/aborted
        msgArray = unwrapMessages(result=result, everClient=getClient())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "receiveRegistrationRequest":
                regResult = msg["TX_DETAILS"]["aborted"]
                self.assertEqual(regResult, True) # Aborted

        # Owner should still be 0
        result = self.domain.getWhois()
        self.assertEqual(result["ownerAddress"], ZERO_ADDRESS)

    # 5. Cleanup
    def test_5(self):
        result = self.domain.TEST_selfdestruct(msig=self.msig, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
# 
class Test_10_CheckWhoisStatistics(unittest.TestCase):       

    msig1              = Multisig(everClient=getClient())
    msig2              = Multisig(everClient=getClient())
    domain_domaino     = DnsRecordTEST(everClient=getClient(), name="domaino",     ownerAddress=msig1.ADDRESS)
    domain_domaino_kek = DnsRecordTEST(everClient=getClient(), name="domaino/kek", ownerAddress=msig2.ADDRESS)
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain_domaino.ADDRESS,     EVER * 2)
        giverGive(getClient(), self.domain_domaino_kek.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig1.ADDRESS,              EVER * 2)
        giverGive(getClient(), self.msig2.ADDRESS,              EVER * 2)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "domaino" and "domaino/kek"
    def test_3(self):
        result = self.domain_domaino.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino_kek.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. change Whois and get Whois
    def test_4(self):
        price = DIME*2

        # Change owners 6 times
        result = self.domain_domaino.changeOwner(msig=self.msig1, newOwnerAddress=self.msig2.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino.changeOwner(msig=self.msig1, newOwnerAddress=self.msig2.ADDRESS)
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 100) # ERROR_MESSAGE_SENDER_IS_NOT_MY_OWNER

        result = self.domain_domaino.changeOwner(msig=self.msig2, newOwnerAddress=self.msig1.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino.changeOwner(msig=self.msig1, newOwnerAddress=self.msig2.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino.changeOwner(msig=self.msig2, newOwnerAddress=self.msig1.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino.changeOwner(msig=self.msig1, newOwnerAddress=self.msig2.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino.changeOwner(msig=self.msig2, newOwnerAddress=self.msig1.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain_domaino.getWhois()
        self.assertEqual(result["totalOwnersNum"], "7")

        # Deny subdomain registration 
        result = self.domain_domaino.changeRegistrationType(msig=self.msig1, newType=3)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain_domaino_kek.claimExpired(msig=self.msig1, newOwnerAddress=self.msig2.ADDRESS)
        self.assertEqual(result["exception"]["errorCode"], 0)
        
        # Check registration result
        msgArray = unwrapMessages(result=result, everClient=getClient())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                regResult = msg["FUNCTION_PARAMS"]["result"]
                self.assertEqual(regResult, "2") # DENIED

        result = self.domain_domaino.getWhois()
        self.assertEqual(result["subdomainRegDenied"], "1")

        # Money registration covers two stats: "subdomainRegAccepted" and "totalFeesCollected"
        result = self.domain_domaino.changeRegistrationType(msig=self.msig1, newType=1)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain_domaino.changeRegistrationPrice(msig=self.msig1, newPrice=price)
        self.assertEqual(result["exception"]["errorCode"], 0)

        # We try to include less money than price
        result = self.domain_domaino_kek.claimExpired(msig=self.msig1, newOwnerAddress=self.msig2.ADDRESS, value=DIME)
        self.assertEqual(result["exception"]["errorCode"], 0)
        
        msgArray = unwrapMessages(result=result, everClient=getClient())
        for msg in msgArray:
            if msg["FUNCTION_NAME"] == "callbackOnRegistrationRequest":
                regResult = msg["FUNCTION_PARAMS"]["result"]
                self.assertEqual(regResult, "3") # NOT_ENOUGH_MONEY

        # Claim
        result = self.domain_domaino_kek.claimExpired(msig=self.msig1, newOwnerAddress=self.msig2.ADDRESS, value=DIME*7)
        self.assertEqual(result["exception"]["errorCode"], 0)
        msgArray = unwrapMessages(result=result, everClient=getClient())

        result = self.domain_domaino.getWhois()
        self.assertEqual(result["subdomainRegAccepted"], "1"       )
        self.assertEqual(result["totalFeesCollected"],   str(price))

        # Check correct owner
        result = self.domain_domaino_kek.getWhois()
        self.assertEqual(result["ownerAddress"], self.msig2.ADDRESS)

    # 5. Cleanup
    def test_5(self):
        result = self.domain_domaino.TEST_selfdestruct(msig=self.msig1, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_domaino_kek.TEST_selfdestruct(msig=self.msig2, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.msig1.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
# 
class Test_11_ChangeWhois(unittest.TestCase):   
    
    msig   = Multisig(everClient=getClient())
    domain = DnsRecordTEST(everClient=getClient(), name="domaino",ownerAddress=msig.ADDRESS)
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig.ADDRESS,   EVER * 2)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "domaino"
    def test_3(self):
        result = self.domain.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. change Whois and get Whois
    def test_4(self):
        endpointAddress = self.msig.ADDRESS
        comment         = "wassup you boyz!!!@@#%"
        
        result = self.domain.changeEndpointAddress(msig=self.msig, newAddress=endpointAddress)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain.changeComment(msig=self.msig, newComment=comment)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain.getWhois()
        self.assertEqual(result["endpointAddress"], endpointAddress     )
        self.assertEqual(result["comment"],         stringToHex(comment))

    # 5. Cleanup
    def test_5(self):
        result = self.domain.TEST_selfdestruct(msig=self.msig, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
# 
class Test_12_ReleaseDomain(unittest.TestCase): 
    
    msig   = Multisig(everClient=getClient())
    domain = DnsRecordTEST(everClient=getClient(), name="dominos", ownerAddress=msig.ADDRESS)
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig.ADDRESS,   EVER * 2)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "dominos"
    def test_3(self):
        result = self.domain.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. change Whois and get Whois
    def test_4(self):
        result = self.domain.releaseDomain(msig=self.msig)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain.getWhois()
        self.assertEqual(result["ownerAddress"],     ZERO_ADDRESS)
        self.assertEqual(result["dtExpires"],        "0"         )
        self.assertEqual(result["endpointAddress"],  ZERO_ADDRESS)
        self.assertEqual(result["registrationType"], "3"         )
        self.assertEqual(result["comment"],          ""          )

    # 5. Cleanup
    def test_5(self):
        result = self.domain.TEST_selfdestruct(msig=self.msig, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
# 
class Test_13_ClaimAlreadyClaimed(unittest.TestCase):       

    msig1  = Multisig(everClient=getClient())
    msig2  = Multisig(everClient=getClient())
    domain = DnsRecordTEST(everClient=getClient(), name="domaino", ownerAddress=msig1.ADDRESS)
    
    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig1.ADDRESS,  EVER * 2)
        giverGive(getClient(), self.msig2.ADDRESS,  EVER * 2)
        
    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "domaino"
    def test_3(self):
        result = self.domain.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 4. Try to claim
    def test_4(self):
        # Change to FFA
        result = self.domain.changeRegistrationType(msig=self.msig1, newType=0)
        self.assertEqual(result["exception"]["errorCode"], 0)

        # Try to claim from other multisig
        result = self.domain.claimExpired(msig=self.msig2, newOwnerAddress=self.msig2.ADDRESS)
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 202) # ERROR_DOMAIN_IS_NOT_EXPIRED

    # 5. Cleanup
    def test_5(self):
        result = self.domain.TEST_selfdestruct(msig=self.msig1, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        
        result = self.msig1.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)
        
        result = self.msig2.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
#
class Test_14_LongestName(unittest.TestCase):
    
    msig1        = Multisig(everClient=getClient())
    msig2        = Multisig(everClient=getClient())
    msig3        = Multisig(everClient=getClient())
    msig4        = Multisig(everClient=getClient())
    domain_1     = DnsRecordTEST(everClient=getClient(), ownerAddress=msig1.ADDRESS, name="1234567890123456789012345678901")
    domain_2     = DnsRecordTEST(everClient=getClient(), ownerAddress=msig2.ADDRESS, name="1234567890123456789012345678901/1234567890123456789012345678901")
    domain_3     = DnsRecordTEST(everClient=getClient(), ownerAddress=msig3.ADDRESS, name="1234567890123456789012345678901/1234567890123456789012345678901/1234567890123456789012345678901")
    domain_4     = DnsRecordTEST(everClient=getClient(), ownerAddress=msig4.ADDRESS, name="1234567890123456789012345678901/1234567890123456789012345678901/1234567890123456789012345678901/1234567890123456789012345678901")

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain_1.ADDRESS, EVER * 2)
        giverGive(getClient(), self.domain_2.ADDRESS, EVER * 2)
        giverGive(getClient(), self.domain_3.ADDRESS, EVER * 2)
        giverGive(getClient(), self.domain_4.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig1.ADDRESS,    EVER * 2)
        giverGive(getClient(), self.msig2.ADDRESS,    EVER * 2)
        giverGive(getClient(), self.msig3.ADDRESS,    EVER * 2)
        giverGive(getClient(), self.msig4.ADDRESS,    EVER * 2)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig1.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig2.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig3.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig4.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy domains
    def test_3(self):
        result = self.domain_1.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_2.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_3.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_4.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)

    # 5. Claim
    def test_5(self):

        regPrice = DIME*5

        # 1
        result = self.domain_1.changeRegistrationType(msig=self.msig1, newType=1)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_1.changeRegistrationPrice(msig=self.msig1, newPrice=regPrice)
        self.assertEqual(result["exception"]["errorCode"], 0)
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        # 2
        result = self.domain_2.claimExpired(msig=self.msig2, newOwnerAddress=self.msig2.ADDRESS, value=EVER)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain_2.changeRegistrationType(msig=self.msig2, newType=1)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_2.changeRegistrationPrice(msig=self.msig2, newPrice=regPrice)
        self.assertEqual(result["exception"]["errorCode"], 0)
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        # 3
        result = self.domain_3.claimExpired(msig=self.msig3, newOwnerAddress=self.msig3.ADDRESS, value=EVER)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain_3.changeRegistrationType(msig=self.msig3, newType=1)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_3.changeRegistrationPrice(msig=self.msig3, newPrice=regPrice)
        self.assertEqual(result["exception"]["errorCode"], 0)
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

        # 4
        result = self.domain_4.claimExpired(msig=self.msig4, newOwnerAddress=self.msig4.ADDRESS, value=EVER)
        self.assertEqual(result["exception"]["errorCode"], 0)

        result = self.domain_4.changeRegistrationType(msig=self.msig4, newType=1)
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_4.changeRegistrationPrice(msig=self.msig4, newPrice=regPrice)
        self.assertEqual(result["exception"]["errorCode"], 0)
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, 0)

    # 6. Cleanup
    def test_6(self):
        result = self.domain_1.TEST_selfdestruct(msig=self.msig1, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_2.TEST_selfdestruct(msig=self.msig2, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_3.TEST_selfdestruct(msig=self.msig3, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.domain_4.TEST_selfdestruct(msig=self.msig4, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        
        result = self.msig1.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)        
        result = self.msig2.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)        
        result = self.msig3.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)        
        result = self.msig4.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# ==============================================================================
#
class Test_15_ClaimInvalid(unittest.TestCase):
    
    msig   = Multisig(everClient=getClient())
    domain = DnsRecordTEST(everClient=getClient(), name = "netOVKA", ownerAddress=msig.ADDRESS)

    def test_0(self):
        print("\n\n----------------------------------------------------------------------")
        print("Running:", self.__class__.__name__)

    # 1. Giver
    def test_1(self):
        giverGive(getClient(), self.domain.ADDRESS, EVER * 2)
        giverGive(getClient(), self.msig.ADDRESS,   EVER * 2)

    # 2. Deploy multisig
    def test_2(self):
        result = self.msig.deploy()
        self.assertEqual(result["exception"]["errorCode"], 0)
        
    # 3. Deploy "netOVKA"
    def test_3(self):
        result = self.domain.deploy()
        self.assertEqual(result["exception"]["errorCode"], 200)

    # 4. Try prolongate
    def test_4(self):
        result       = self.domain.claimExpired(msig=self.msig, newOwnerAddress=self.msig.ADDRESS)
        realExitCode = getExitCode(everClient=getClient(), msgIdArray=result["result"].transaction["out_msgs"])
        self.assertEqual(realExitCode, -10) # -10, we didn't even start checking modifiers
        
    # 5. Cleanup
    def test_5(self):
        result = self.domain.TEST_selfdestruct(msig=self.msig, dest=ever_utils.giverGetAddress())
        self.assertEqual(result["exception"]["errorCode"], 0)
        result = self.msig.sendTransaction(addressDest=ever_utils.giverGetAddress(), value=0, flags=128)
        self.assertEqual(result["exception"]["errorCode"], 0)

# TODO: add deploying from debot

# ==============================================================================
# 
unittest.main()
