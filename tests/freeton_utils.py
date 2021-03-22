#!/usr/bin/env python3

# ==============================================================================
# 
import asyncio
import os
import json
import argparse
import logging
import base64
import time
from tonclient.client import *
from tonclient.types  import *
from binascii import unhexlify
import pathlib

# ==============================================================================
# 
client_config = ClientConfig()
#client_config.network.server_address = "https://main.ton.dev"
client_config.network.server_address = "http://192.168.0.80"
asyncClient   = TonClient(config=client_config)
ZERO_PUBKEY   =   "0000000000000000000000000000000000000000000000000000000000000000"
ZERO_ADDRESS  = "0:0000000000000000000000000000000000000000000000000000000000000000"

# ==============================================================================
# 
def getAbi(abiPath):
    abi = Abi.from_path(path=abiPath)
    return abi

def getTvc(tvcPath):
    fp       = open(tvcPath, 'rb')
    tvc      = base64.b64encode(fp.read()).decode()
    return tvc

def getLocalVariables(abiPath, tvcPath):
    return (getAbi(abiPath), getTvc(tvcPath))


# ==============================================================================
#
def getCodeFromTvc(tvcPath):
    tvc           = getTvc(tvcPath)
    tvcCodeParams = ParamsOfGetCodeFromTvc(tvc=tvc)
    tvcCodeResult = asyncClient.boc.get_code_from_tvc(params=tvcCodeParams).code
    return tvcCodeResult

# ==============================================================================
#
# abiPath       - path to file;
# tvcPath       - path to file;
# keys          - KeyPair class;
# initialPubkey - 
# initialData   - 
#
def getAddress(abiPath, tvcPath, keys, initialPubkey, initialData):

    (abi, tvc) = getLocalVariables(abiPath, tvcPath)
    signer     = Signer.Keys(keys)
    deploySet  = DeploySet(tvc=tvc, initial_pubkey=initialPubkey, initial_data=initialData)

    params     = ParamsOfEncodeMessage(abi=abi, signer=signer, deploy_set=deploySet)
    encoded    = asyncClient.abi.encode_message(params=params)

    return encoded.address

# ==============================================================================
#
# abiPath       - path to file;
# tvcPath       - path to file;
# initialData   - 
#
def getAddressZeroPubkey(abiPath, tvcPath, initialData):
    keys = KeyPair(ZERO_PUBKEY, ZERO_PUBKEY)
    return getAddress(abiPath, tvcPath, keys, ZERO_PUBKEY, initialData)

# ==============================================================================
#
def deployContract():
    (abi, tvc) = getLocalVariables(abiPath, tvcPath)
    code       = getCodeFromTvc(abiPath, tvcPath)
    # TODO
    #call_set   = CallSet(function_name='constructor', input={"ownerAddress":ZERO_ADDRESS, "ownerPubkey":ZERO_PUBKEY})

# ==============================================================================
#
def callFunction(abiPath, contractAddress, functionName, keysFile, functionInputs):

    if keysFile == "":
        signer = Signer.External(ZERO_PUBKEY)
    else:
        signer = Signer.Keys(KeyPair.load(keysFile, False))

    abi        = getAbi(abiPath)
    callSet    = CallSet(function_name=functionName, input=functionInputs)
    params     = ParamsOfEncodeMessage(abi=abi, address=contractAddress, signer=signer, call_set=callSet)
    encoded    = asyncClient.abi.encode_message(params=params)

    message_params = ParamsOfSendMessage(message=encoded.message, send_events=False, abi=abi)
    message_result = asyncClient.processing.send_message(params=message_params)

    wait_params    = ParamsOfWaitForTransaction(message=encoded.message, shard_block_id=message_result.shard_block_id, send_events=False, abi=abi)
    result         = asyncClient.processing.wait_for_transaction(params=wait_params)
    # possibly interesting fields:
    result.transaction["compute"]["success"]
    result.transaction["compute"]["exit_code"]
    result.transaction["compute"]["gas_used"]
    result.transaction["action"]["success"]
    result.transaction["action"]["valid"]
    result.transaction["action"]["result_code"]

    return result

# ==============================================================================
#
def giverGive(contractAddress, amountTons):
    giverAddress = "0:841288ed3b55d9cdafa806807f02a0ae0c169aa5edfe88a789a6482429756a94"
    callFunction("local_giver.abi.json", giverAddress, "sendGrams", "", {"dest":contractAddress,"amount":amountTons})

# ==============================================================================
#
