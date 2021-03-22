#!/usr/bin/env python3

# ==============================================================================
# 
from freeton_utils import *

# ==============================================================================
# 

ABI      = "../contracts/DnsRecord.abi.json"
TVC      = "../contracts/DnsRecord.tvc"
code     = getCodeFromTvc(TVC)
initData = {"_domainName":"656565","_domainCode": code}
address  = getAddressZeroPubkey(ABI, TVC, initData)
print(address)

giverGive("0:08d0a4940a056c3f85c0364261ef4e3316e11240bd2cc9b4f767f12200b634be", 1000000000)