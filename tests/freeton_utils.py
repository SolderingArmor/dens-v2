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
import ast

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
def stringToHex(inputString):
    return "".join(hex(ord(x))[2:] for x in inputString)

# ==============================================================================
#
def getValuesFromException(tonException):
    arg       = tonException.args[0]
    error     = arg[arg.find("(Data:") + 7 : - 1]
    result    = ast.literal_eval(error)
    errorCode = result["exit_code"]
    errorDesc = result["description"]
    transID   = result["transaction_id"]
    return (errorCode, errorDesc, transID)


# ==============================================================================
#
def getCodeFromTvc(tvcPath):
    tvc           = getTvc(tvcPath)
    tvcCodeParams = ParamsOfGetCodeFromTvc(tvc=tvc)
    tvcCodeResult = asyncClient.boc.get_code_from_tvc(params=tvcCodeParams).code
    return tvcCodeResult

# ==============================================================================
#
def getSigner(keysFile):
    if keysFile == "":
        signer = Signer.External(ZERO_PUBKEY)
    else:
        signer = Signer.Keys(KeyPair.load(keysFile, False))
    return signer

# ==============================================================================
#
# abiPath       - path to file;
# tvcPath       - path to file;
# signer        - 
# initialPubkey - 
# initialData   - 
#
def getAddress(abiPath, tvcPath, signer, initialPubkey, initialData):

    (abi, tvc) = getLocalVariables(abiPath, tvcPath)
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
    keys   = KeyPair(ZERO_PUBKEY, ZERO_PUBKEY)
    signer = Signer.Keys(keys)
    return getAddress(abiPath, tvcPath, signer, ZERO_PUBKEY, initialData)

# ==============================================================================
# 
def deployContract(abiPath, tvcPath, constructorInput, initialData, signer, initialPubkey):

    try:
        (abi, tvc) = getLocalVariables(abiPath, tvcPath)
        callSet    = CallSet(function_name='constructor', input=constructorInput)
        deploySet  = DeploySet(tvc=tvc, initial_pubkey=initialPubkey, initial_data=initialData)
        params     = ParamsOfEncodeMessage(abi=abi, signer=signer, call_set=callSet, deploy_set=deploySet)
        encoded    = asyncClient.abi.encode_message(params=params)

        messageParams = ParamsOfSendMessage(message=encoded.message, send_events=False, abi=abi)
        messageResult = asyncClient.processing.send_message(params=messageParams)
        waitParams    = ParamsOfWaitForTransaction(message=encoded.message, shard_block_id=messageResult.shard_block_id, send_events=False, abi=abi)
        result        = asyncClient.processing.wait_for_transaction(params=waitParams)

        #print(result.transaction)
        return (result, 0, "", "")

    except TonException as ton:
        (errorCode, errorDesc, transID) = getValuesFromException(ton)
        return ({}, errorCode, errorDesc, transID)

# ==============================================================================
#
def runFunction(abiPath, contractAddress, functionName, functionInputs):

    paramsQuery = ParamsOfQuery(query='query($acc: String){accounts(filter:{id:{eq:$acc}}){boc}}', variables={'acc': contractAddress})
    result = asyncClient.net.query(params=paramsQuery)
    boc = result.result["data"]["accounts"][0]["boc"]
    
    abi        = getAbi(abiPath)
    callSet    = CallSet(function_name=functionName, input=functionInputs)
    params     = ParamsOfEncodeMessage(abi=abi, address=contractAddress, signer=Signer.NoSigner(), call_set=callSet)
    encoded    = asyncClient.abi.encode_message(params=params)
    paramsRun  = ParamsOfRunTvm(message=encoded.message, account=boc, abi=abi)
    result     = asyncClient.tvm.run_tvm(params=paramsRun)

    paramsDcd  = ParamsOfDecodeMessage(abi=abi, message=result.out_messages[0])
    decoded    = asyncClient.abi.decode_message(params=paramsDcd)

    result = decoded.value["value0"]
    return result

# ==============================================================================
#
def callFunction(abiPath, contractAddress, functionName, signer, functionInputs):

    try:
        abi        = getAbi(abiPath)
        callSet    = CallSet(function_name=functionName, input=functionInputs)
        params     = ParamsOfEncodeMessage(abi=abi, address=contractAddress, signer=signer, call_set=callSet)
        encoded    = asyncClient.abi.encode_message(params=params)

        message_params = ParamsOfSendMessage(message=encoded.message, send_events=False, abi=abi)
        message_result = asyncClient.processing.send_message(params=message_params)

        wait_params    = ParamsOfWaitForTransaction(message=encoded.message, shard_block_id=message_result.shard_block_id, send_events=False, abi=abi)
        result         = asyncClient.processing.wait_for_transaction(params=wait_params)
        # possibly interesting fields:
        # result.transaction
        # result.transaction["aborted"]
        # result.transaction["out_msgs"]
        # result.transaction["compute"]["success"]
        # result.transaction["compute"]["exit_code"]
        # result.transaction["compute"]["gas_used"]
        # result.transaction["action"]["success"]
        # result.transaction["action"]["valid"]
        # result.transaction["action"]["result_code"]    
        return (result, 0, "", "")

    except TonException as ton:
        (errorCode, errorDesc, transID) = getValuesFromException(ton)
        return ({}, errorCode, errorDesc, transID)

# ==============================================================================
#
def giverGive(contractAddress, amountTons):
    giverAddress = "0:841288ed3b55d9cdafa806807f02a0ae0c169aa5edfe88a789a6482429756a94"
    signer = getSigner("")
    callFunction("local_giver.abi.json", giverAddress, "sendGrams", signer, {"dest":contractAddress,"amount":amountTons})

# ==============================================================================
#
