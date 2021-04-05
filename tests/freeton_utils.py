#!/usr/bin/env python3

# ==============================================================================
# 
import asyncio
import sys
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
from datetime import datetime

# ==============================================================================
# 
clientConfig  = ClientConfig()
clientConfig.network.server_address = "https://net.ton.dev"
asyncClient   = TonClient(config=clientConfig)
ZERO_PUBKEY   =   "0000000000000000000000000000000000000000000000000000000000000000"
ZERO_ADDRESS  = "0:0000000000000000000000000000000000000000000000000000000000000000"
USE_GIVER     = True
THROW         = False

# ==============================================================================
# 
def changeConfig(httpAddress, useGiver, throw):

    global asyncClient
    global USE_GIVER
    global THROW
    if httpAddress != "":
        config      = ClientConfig()
        config.network.server_address = httpAddress
        asyncClient = TonClient(config=config)
    USE_GIVER = useGiver
    THROW     = throw

# ==============================================================================
# 
def getAbi(abiPath):
    abi = Abi.from_path(path=abiPath)
    return abi

def getTvc(tvcPath):
    fp  = open(tvcPath, 'rb')
    tvc = base64.b64encode(fp.read()).decode()
    fp.close()
    return tvc

def getLocalVariables(abiPath, tvcPath):
    return (getAbi(abiPath), getTvc(tvcPath))


# ==============================================================================
#
def stringToHex(inputString):
    return "".join(hex(ord(x))[2:] for x in inputString)

# ==============================================================================
#
def getNowTimestamp():
    dt = datetime.now()
    unixtime = round(dt.timestamp())
    return unixtime

# ==============================================================================
#
def getValuesFromException(tonException):
    arg    = tonException.args[0]
    error  = arg[arg.find("(Data:") + 7 : - 1]
    result = ast.literal_eval(error)

    try:
        errorCode = result["exit_code"]
    except KeyError:
        errorCode = ""

    try:
        errorDesc = result["description"]
    except KeyError:
        errorDesc = ""

    try:
        transID = result["transaction_id"]
    except KeyError:
        transID = ""

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
def loadSigner(keysFile):
    if keysFile == "":
        signer = Signer.External(ZERO_PUBKEY)
    else:
        signer = Signer.Keys(KeyPair.load(keysFile, False))
    return signer

def generateSigner():
    keypair = asyncClient.crypto.generate_random_sign_keys()
    signer  = Signer.Keys(keys=keypair)
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
        (abi, tvc)    = getLocalVariables(abiPath, tvcPath)
        callSet       = CallSet(function_name='constructor', input=constructorInput)
        deploySet     = DeploySet(tvc=tvc, initial_pubkey=initialPubkey, initial_data=initialData)
        params        = ParamsOfEncodeMessage(abi=abi, signer=signer, call_set=callSet, deploy_set=deploySet)
        encoded       = asyncClient.abi.encode_message(params=params)

        messageParams = ParamsOfSendMessage(message=encoded.message, send_events=False, abi=abi)
        messageResult = asyncClient.processing.send_message(params=messageParams)
        waitParams    = ParamsOfWaitForTransaction(message=encoded.message, shard_block_id=messageResult.shard_block_id, send_events=False, abi=abi)
        result        = asyncClient.processing.wait_for_transaction(params=waitParams)

        #print(result.transaction)
        return (result, 0, "", "")

    except TonException as ton:
        if THROW:
            raise ton
        (errorCode, errorDesc, transID) = getValuesFromException(ton)
        return ({}, errorCode, errorDesc, transID)

# ==============================================================================
#
def runFunction(abiPath, contractAddress, functionName, functionParams):

    paramsQuery  = ParamsOfQuery(query="query($acc: String){accounts(filter:{id:{eq:$acc}}){boc}}", variables={"acc": contractAddress})
    result       = asyncClient.net.query(params=paramsQuery)
    boc          = result.result["data"]["accounts"][0]["boc"]
    
    abi          = getAbi(abiPath)
    callSet      = CallSet(function_name=functionName, input=functionParams)
    params       = ParamsOfEncodeMessage(abi=abi, address=contractAddress, signer=Signer.NoSigner(), call_set=callSet)
    encoded      = asyncClient.abi.encode_message(params=params)

    paramsRun    = ParamsOfRunTvm(message=encoded.message, account=boc, abi=abi)
    result       = asyncClient.tvm.run_tvm(params=paramsRun)

    paramsDecode = ParamsOfDecodeMessage(abi=abi, message=result.out_messages[0])
    decoded      = asyncClient.abi.decode_message(params=paramsDecode)

    result = decoded.value["value0"]
    return result

# ==============================================================================
#
def callFunction(abiPath, contractAddress, functionName, functionParams, signer):

    try:
        abi           = getAbi(abiPath)
        callSet       = CallSet(function_name=functionName, input=functionParams)
        params        = ParamsOfEncodeMessage(abi=abi, address=contractAddress, signer=signer, call_set=callSet)
        encoded       = asyncClient.abi.encode_message(params=params)

        messageParams = ParamsOfSendMessage(message=encoded.message, send_events=False, abi=abi)
        messageResult = asyncClient.processing.send_message(params=messageParams)

        waitParams    = ParamsOfWaitForTransaction(message=encoded.message, shard_block_id=messageResult.shard_block_id, send_events=False, abi=abi)
        result        = asyncClient.processing.wait_for_transaction(params=waitParams)
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
        if THROW:
            raise ton
        (errorCode, errorDesc, transID) = getValuesFromException(ton)
        return ({}, errorCode, errorDesc, transID)

# ==============================================================================
#
def decodeMessageBody(boc, possibleAbiFiles):
    for abi in possibleAbiFiles:
        try:
            params = ParamsOfDecodeMessageBody(abi=getAbi(abi), body=boc, is_internal=True)
            result = asyncClient.abi.decode_message_body(params=params)
            return (abi, result)

        except TonException as ton:
            pass

    return ("", "")

def getMessageGraphQL(messageID, fields):
    paramsQuery = ParamsOfQuery(query="query($msg: String){messages(filter:{id:{eq:$msg}}){" + fields + "}}", variables={"msg": messageID})
    result      = asyncClient.net.query(params=paramsQuery)
    
    if len(result.result["data"]["messages"]) > 0:
        return result.result["data"]["messages"][0]
    else:
        return ""

def getTransactionGraphQL(messageID, fields):
    #paramsQuery = ParamsOfQuery(query="query($msg: String){transactions(filter:{in_msg:{eq:$msg}}){aborted,compute{exit_arg, exit_code, skipped_reason, skipped_reason_name}}}", variables={"msg": messageID})
    paramsQuery = ParamsOfQuery(query="query($msg: String){transactions(filter:{in_msg:{eq:$msg}}){" + fields + "}}", variables={"msg": messageID})
    result      = asyncClient.net.query(params=paramsQuery)

    if len(result.result["data"]["transactions"]) > 0:
        return result.result["data"]["transactions"][0]
    else:
        return ""

def getExitCodeFromMessageID(messageID, fields):
    result       = getTransactionGraphQL(messageID, fields)
    #realExitCode = result.result["data"]["transactions"][0]["compute"]["exit_code"]
    realExitCode = result["compute"]["exit_code"]
    return realExitCode

# ==============================================================================
#
def _unwrapMessages(messageID, parentMessageID, abiFilesArray):

    messageFilters     = "id, src, dst, body"
    transactionFilters = "out_msgs, aborted, compute{exit_arg, exit_code, skipped_reason, skipped_reason_name}"

    resultMsg                = getMessageGraphQL(messageID, messageFilters)
    if resultMsg == "":
        return []        
    (abi, resultMessageBody) = decodeMessageBody(resultMsg["body"], abiFilesArray)
    resultTransaction        = getTransactionGraphQL(messageID, transactionFilters)

    arrayMsg = [{
        "SOURCE":             resultMsg["src"],
        "DEST":               resultMsg["dst"],
        "MESSAGE_ID:":        messageID,
        "PARENT_MESSAGE_ID:": parentMessageID,
        "TARGE_ABI":          abi,
        "CALL_TYPE":          resultMessageBody.body_type   if resultMessageBody != "" else "---",
        "FUNCTION_NAME":      resultMessageBody.name        if resultMessageBody != "" else "---",
        "FUNCTION_PARAMS":    resultMessageBody.value       if resultMessageBody != "" else "---",
        "MSG_HEADER":         resultMessageBody.header      if resultMessageBody != "" else "---",
        "OUT_MSGS":           resultTransaction["out_msgs"] if resultTransaction != "" else [],
        "TX_DETAILS":         resultTransaction,
    }]

    if resultTransaction != "":
        for msg in resultTransaction["out_msgs"]:
            arrayResult = _unwrapMessages(msg, messageID, abiFilesArray)
            arrayMsg   += arrayResult
    
    return arrayMsg

def unwrapMessages(messageIdArray, abiFilesArray):
    arrayMsg = []
    for msg in messageIdArray:
        arrayResult = _unwrapMessages(msg, "", abiFilesArray)
        arrayMsg   += arrayResult
    
    return arrayMsg

# ==============================================================================
#
def giverGive(contractAddress, amountTons):
    
    if not USE_GIVER:
        print("\nNow GIVER expects to give {} TONs to address {};".format(amountTons, contractAddress))
        input("Please, do it manually and then press ENTER to continue...")
        return
    
    giverAddress = "0:841288ed3b55d9cdafa806807f02a0ae0c169aa5edfe88a789a6482429756a94"
    callFunction("../bin/local_giver.abi.json", giverAddress, "sendGrams", {"dest":contractAddress,"amount":amountTons}, Signer.NoSigner())

# ==============================================================================
#
