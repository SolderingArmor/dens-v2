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
#clientConfig  = ClientConfig()
#clientConfig.network.server_address = "https://net.ton.dev"
#asyncClient   = TonClient(config=clientConfig)
ZERO_PUBKEY   =   "0000000000000000000000000000000000000000000000000000000000000000"
ZERO_ADDRESS  = "0:0000000000000000000000000000000000000000000000000000000000000000"
MSIG_GIVER    = ""
USE_GIVER     = True
THROW         = False

# ==============================================================================
# 
def changeConfig(httpAddress, useGiver, throw):

    #global asyncClient
    global USE_GIVER
    global THROW
    #if httpAddress != "":
    #    config      = ClientConfig()
    #    config.network.server_address = httpAddress
    #    asyncClient = TonClient(config=config)
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

def getAbiTvc(abiPath, tvcPath):
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
def getCodeFromTvc(tonClient, tvcPath):
    tvc           = getTvc(tvcPath)
    tvcCodeParams = ParamsOfGetCodeFromTvc(tvc=tvc)
    tvcCodeResult = tonClient.boc.get_code_from_tvc(params=tvcCodeParams).code
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
    keypair = TonClient(config=ClientConfig()).crypto.generate_random_sign_keys()
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
def getAddress(tonClient, abiPath, tvcPath, signer, initialPubkey, initialData):

    (abi, tvc) = getAbiTvc(abiPath, tvcPath)
    deploySet  = DeploySet(tvc=tvc, initial_pubkey=initialPubkey, initial_data=initialData)

    params     = ParamsOfEncodeMessage(abi=abi, signer=signer, deploy_set=deploySet)
    encoded    = tonClient.abi.encode_message(params=params)

    return encoded.address

# ==============================================================================
#
# abiPath       - path to file;
# tvcPath       - path to file;
# initialData   - 
#
def getAddressZeroPubkey(tonClient, abiPath, tvcPath, initialData):
    keys   = KeyPair(ZERO_PUBKEY, ZERO_PUBKEY)
    signer = Signer.Keys(keys)
    return getAddress(tonClient, abiPath, tvcPath, signer, ZERO_PUBKEY, initialData)

# ==============================================================================
# 
def deployContract(tonClient, abiPath, tvcPath, constructorInput, initialData, signer, initialPubkey):

    try:
        (abi, tvc)    = getAbiTvc(abiPath, tvcPath)
        callSet       = CallSet(function_name='constructor', input=constructorInput)
        deploySet     = DeploySet(tvc=tvc, initial_pubkey=initialPubkey, initial_data=initialData)
        params        = ParamsOfEncodeMessage(abi=abi, signer=signer, call_set=callSet, deploy_set=deploySet)
        encoded       = tonClient.abi.encode_message(params=params)

        messageParams = ParamsOfSendMessage(message=encoded.message, send_events=False, abi=abi)
        messageResult = tonClient.processing.send_message(params=messageParams)
        waitParams    = ParamsOfWaitForTransaction(message=encoded.message, shard_block_id=messageResult.shard_block_id, send_events=False, abi=abi)
        result        = tonClient.processing.wait_for_transaction(params=waitParams)

        #print(result.transaction)
        return (result, 0, "", "")

    except TonException as ton:
        if THROW:
            raise ton
        (errorCode, errorDesc, transID) = getValuesFromException(ton)
        return ({}, errorCode, errorDesc, transID)

# ==============================================================================
#
def runFunction(tonClient, abiPath, contractAddress, functionName, functionParams):

    result       = getAccountGraphQL(tonClient, contractAddress, "boc")
    if result == "":
        return ""

    boc          = result["boc"]
    abi          = getAbi(abiPath)
    callSet      = CallSet(function_name=functionName, input=functionParams)
    params       = ParamsOfEncodeMessage(abi=abi, address=contractAddress, signer=Signer.NoSigner(), call_set=callSet)
    encoded      = tonClient.abi.encode_message(params=params)

    paramsRun    = ParamsOfRunTvm(message=encoded.message, account=boc, abi=abi)
    result       = tonClient.tvm.run_tvm(params=paramsRun)

    paramsDecode = ParamsOfDecodeMessage(abi=abi, message=result.out_messages[0])
    decoded      = tonClient.abi.decode_message(params=paramsDecode)

    result = decoded.value["value0"]
    return result

# ==============================================================================
#
def callFunction(tonClient, abiPath, contractAddress, functionName, functionParams, signer):

    try:
        abi           = getAbi(abiPath)
        callSet       = CallSet(function_name=functionName, input=functionParams)
        params        = ParamsOfEncodeMessage(abi=abi, address=contractAddress, signer=signer, call_set=callSet)
        encoded       = tonClient.abi.encode_message(params=params)

        messageParams = ParamsOfSendMessage(message=encoded.message, send_events=False, abi=abi)
        messageResult = tonClient.processing.send_message(params=messageParams)

        waitParams    = ParamsOfWaitForTransaction(message=encoded.message, shard_block_id=messageResult.shard_block_id, send_events=False, abi=abi)
        result        = tonClient.processing.wait_for_transaction(params=waitParams)
        return (result, 0, "", "")

    except TonException as ton:
        if THROW:
            raise ton
        (errorCode, errorDesc, transID) = getValuesFromException(ton)
        return ({}, errorCode, errorDesc, transID)

# ==============================================================================
#
def decodeMessageBody(tonClient, boc, possibleAbiFiles):
    for abi in possibleAbiFiles:
        try:
            params = ParamsOfDecodeMessageBody(abi=getAbi(abi), body=boc, is_internal=True)
            result = tonClient.abi.decode_message_body(params=params)
            return (abi, result)

        except TonException as ton:
            pass

    return ("", "")

def getAccountGraphQL(tonClient, accountID, fields):
    paramsQuery = ParamsOfQuery(query="query($accnt: String){accounts(filter:{id:{eq:$accnt}}){" + fields + "}}", variables={"accnt": accountID})
    result      = tonClient.net.query(params=paramsQuery)
    
    if len(result.result["data"]["accounts"]) > 0:
        return result.result["data"]["accounts"][0]
    else:
        return ""

def getMessageGraphQL(tonClient, messageID, fields):
    paramsQuery = ParamsOfQuery(query="query($msg: String){messages(filter:{id:{eq:$msg}}){" + fields + "}}", variables={"msg": messageID})
    result      = tonClient.net.query(params=paramsQuery)
    
    if len(result.result["data"]["messages"]) > 0:
        return result.result["data"]["messages"][0]
    else:
        return ""

def getTransactionGraphQL(tonClient, messageID, fields):
    paramsQuery = ParamsOfQuery(query="query($msg: String){transactions(filter:{in_msg:{eq:$msg}}){" + fields + "}}", variables={"msg": messageID})
    result      = tonClient.net.query(params=paramsQuery)

    if len(result.result["data"]["transactions"]) > 0:
        return result.result["data"]["transactions"][0]
    else:
        return ""

def getExitCodeFromMessageID(tonClient, messageID, fields):
    result       = getTransactionGraphQL(tonClient, messageID, fields)
    realExitCode = result["compute"]["exit_code"]
    return realExitCode

# ==============================================================================
#
def _unwrapMessages(tonClient, messageID, parentMessageID, abiFilesArray):

    messageFilters     = "id, src, dst, body, value(format:DEC), ihr_fee(format:DEC), import_fee(format:DEC), fwd_fee(format:DEC)"
    transactionFilters = "out_msgs, aborted, compute{exit_arg, exit_code, skipped_reason, skipped_reason_name, gas_fees(format:DEC)}, total_fees(format:DEC), storage{storage_fees_collected(format:DEC)}"

    resultMsg                = getMessageGraphQL(tonClient, messageID, messageFilters)
    if resultMsg == "":
        return []        
    (abi, resultMessageBody) = decodeMessageBody(tonClient, resultMsg["body"], abiFilesArray)
    resultTransaction        = getTransactionGraphQL(tonClient, messageID, transactionFilters)

    arrayMsg = [{
        "SOURCE":             resultMsg["src"],
        "DEST":               resultMsg["dst"],
        "VALUE":              resultMsg["value"],
        "FEES":               {"ihr_fee":resultMsg["ihr_fee"], "import_fee":resultMsg["import_fee"], "fwd_fee":resultMsg["fwd_fee"]},
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
            arrayResult = _unwrapMessages(tonClient, msg, messageID, abiFilesArray)
            arrayMsg   += arrayResult
    
    return arrayMsg

def unwrapMessages(tonClient, messageIdArray, abiFilesArray):
    arrayMsg = []
    for msg in messageIdArray:
        arrayResult = _unwrapMessages(tonClient, msg, "", abiFilesArray)
        arrayMsg   += arrayResult
    
    return arrayMsg

# ==============================================================================
#
def giverGive(tonClient, contractAddress, amountTons):
    
    if not USE_GIVER:
        print("\nNow GIVER expects to give {} TONs to address {};".format(amountTons, contractAddress))
        input("Please, do it manually and then press ENTER to continue...")
        return
    
    if MSIG_GIVER == "":
        giverAddress = "0:841288ed3b55d9cdafa806807f02a0ae0c169aa5edfe88a789a6482429756a94"
        callFunction(tonClient, "../bin/local_giver.abi.json", giverAddress, "sendGrams", {"dest":contractAddress,"amount":amountTons}, Signer.NoSigner())
    else:
        ABI     = "../bin/SetcodeMultisigWallet.abi.json"
        TVC     = "../bin/SetcodeMultisigWallet.tvc"
        signer  = loadSigner(MSIG_GIVER)
        address = getAddress(tonClient=tonClient, abiPath=ABI, tvcPath=TVC, signer=signer, initialPubkey=signer.keys.public, initialData={})
        callFunction(tonClient=tonClient, abiPath=ABI, contractAddress=address, functionName="sendTransaction", functionParams={"dest":contractAddress, "value":amountTons, "bounce":False, "flags":1, "payload":""}, signer=signer)

# ==============================================================================
#
