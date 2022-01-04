#!/usr/bin/env python3

# ==============================================================================
# 
import ever_utils
from   ever_utils import *
from   contract_DnsRecord import DnsRecord
from   pprint import pprint

SERVER_ADDRESS = "http://localhost"
#SERVER_ADDRESS = "https://net.ton.dev"
#SERVER_ADDRESS = "https://gql.custler.net"

# ==============================================================================
#
def getClient():
    return getEverClient(testnet=False, customServer=SERVER_ADDRESS)

# ==============================================================================
# 
# Create a Multisig class with a random keypair
msig = Multisig(everClient=getClient())

# Create a DnsRecord class with "freeton" name
domain = DnsRecord(everClient=getClient(), name="everscale", ownerAddress=msig.ADDRESS)


# If you want Multisig with a keypair from file, use this syntax:
#msig = Multisig(signer=loadSigner(keysFile="msig.json"))

# Giver for TON OS SE
giverGive(everClient=getClient(), contractAddress=domain.ADDRESS, amountEvers=EVER*2)
giverGive(everClient=getClient(), contractAddress=msig.ADDRESS,   amountEvers=EVER*2)

# Deploy DnsRecord with SetcodeMultisig address as owner;
result = msig.deploy()
result = domain.deploy()
unwrapMessages(result=result, everClient=getClient())

# Claim domain; this is not needed for top-level domains;
# Change "value=TON" to the required amount; don't forget to add extra 0.5 TON to pay all fes, all change will be returned to SetcodeMultisig;
result = domain.claimExpired(msig=msig, newOwnerAddress=msig.ADDRESS)
unwrapMessages(result=result, everClient=getClient())

# Check Whois
result = domain.getWhois()
pprint(result)

# To call any DnsRecord function from Multisig use this syntax:
#domain.changeComment(msig=msig, newComment="custom comment")