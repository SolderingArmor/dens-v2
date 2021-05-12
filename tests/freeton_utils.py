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
from pprint import pprint

# ==============================================================================
# 
ZERO_PUBKEY   =   "0000000000000000000000000000000000000000000000000000000000000000"
ZERO_ADDRESS  = "0:0000000000000000000000000000000000000000000000000000000000000000"
MSIG_GIVER    = ""
USE_GIVER     = True
THROW         = False

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
    return str(inputString).encode('utf-8').hex()

def hexToString(inputHex):
    return bytearray.fromhex(inputHex).decode()

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
    error  = arg[arg.find("(Data:") + 7 : -1]
    result = ast.literal_eval(error)

    try:
        errorCode = result["exit_code"]
    except KeyError:
        try:
            errorCode = result["local_error"]["data"]["exit_code"]
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

    try:
        message = result["message"]
    except KeyError:
        try:
            message = result["local_error"]["message"]
        except KeyError:
            message = ""

    return {"errorCode":errorCode, "errorMessage":message, "transactionID": transID, "errorDesc": errorDesc}


# ==============================================================================
#
def getCodeFromTvc(tvcPath):

    tonClient     = TonClient(config=ClientConfig())
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
def getAddress(abiPath, tvcPath, signer, initialPubkey, initialData):

    tonClient  = TonClient(config=ClientConfig())
    (abi, tvc) = getAbiTvc(abiPath, tvcPath)
    deploySet  = DeploySet(tvc=tvc, initial_pubkey=initialPubkey, initial_data=initialData)

    params     = ParamsOfEncodeMessage(abi=abi, signer=signer, deploy_set=deploySet)
    encoded    = tonClient.abi.encode_message(params=params)

    return encoded.address

# ==============================================================================
#
def getAddressZeroPubkey(abiPath, tvcPath, initialData):

    keys   = KeyPair(ZERO_PUBKEY, ZERO_PUBKEY)
    signer = Signer.Keys(keys)
    return getAddress(abiPath, tvcPath, signer, ZERO_PUBKEY, initialData)

def prepareMessageBoc(abiPath, functionName, functionParams):

    tonClient = TonClient(config=ClientConfig())
    callSet   = CallSet(function_name=functionName, input=functionParams)
    params    = ParamsOfEncodeMessageBody(abi=getAbi(abiPath), signer=Signer.NoSigner(), is_internal=True, call_set=callSet)
    encoded   = tonClient.abi.encode_message_body(params=params)
    return encoded.body

# ==============================================================================
# 
def deployContract(tonClient: TonClient, abiPath, tvcPath, constructorInput, initialData, signer, initialPubkey):

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
        return (result, {"errorCode":0, "errorMessage":"", "transactionID": "", "errorDesc": ""})

    except TonException as ton:
        if THROW:
            raise ton
        exceptionDetails = getValuesFromException(ton)
        return ({}, exceptionDetails)

# ==============================================================================
#
def runFunction(tonClient: TonClient, abiPath, contractAddress, functionName, functionParams):

    result       = getAccountGraphQL(tonClient, contractAddress, "boc")
    if result == "":
        return ""
    if result["boc"] is None:
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
def callFunction(tonClient: TonClient, abiPath, contractAddress, functionName, functionParams, signer):

    try:
        abi           = getAbi(abiPath)
        callSet       = CallSet(function_name=functionName, input=functionParams)
        params        = ParamsOfEncodeMessage(abi=abi, address=contractAddress, signer=signer, call_set=callSet)
        encoded       = tonClient.abi.encode_message(params=params)

        messageParams = ParamsOfSendMessage(message=encoded.message, send_events=False, abi=abi)
        messageResult = tonClient.processing.send_message(params=messageParams)

        waitParams    = ParamsOfWaitForTransaction(message=encoded.message, shard_block_id=messageResult.shard_block_id, send_events=False, abi=abi)
        result        = tonClient.processing.wait_for_transaction(params=waitParams)

        return (result, {"errorCode":0, "errorMessage":"", "transactionID": "", "errorDesc": ""})

    except TonException as ton:
        if THROW:
            raise ton
        (errorCode, errorDesc, transID) = getValuesFromException(ton)
        return ({}, errorCode, errorDesc, transID)

# ==============================================================================
#
def decodeMessageBody(boc, possibleAbiFiles):

    tonClient = TonClient(config=ClientConfig())

    # EXTERNAL
    for abi in possibleAbiFiles:
        try:
            params = ParamsOfDecodeMessageBody(abi=getAbi(abi), body=boc, is_internal=False)
            result = tonClient.abi.decode_message_body(params=params)
            return (abi, result)

        except TonException as ton:
            pass

    # INTERNAL
    for abi in possibleAbiFiles:
        try:
            params = ParamsOfDecodeMessageBody(abi=getAbi(abi), body=boc, is_internal=True)
            result = tonClient.abi.decode_message_body(params=params)
            return (abi, result)

        except TonException as ton:
            pass

    return ("", "")

def getAccountGraphQL(tonClient: TonClient, accountID, fields):

    paramsQuery = ParamsOfQuery(query="query($accnt: String){accounts(filter:{id:{eq:$accnt}}){" + fields + "}}", variables={"accnt": accountID})
    result      = tonClient.net.query(params=paramsQuery)
    
    if len(result.result["data"]["accounts"]) > 0:
        return result.result["data"]["accounts"][0]
    else:
        return ""

def getMessageGraphQL(tonClient: TonClient, messageID, fields):

    paramsQuery = ParamsOfQuery(query="query($msg: String){messages(filter:{id:{eq:$msg}}){" + fields + "}}", variables={"msg": messageID})
    result      = tonClient.net.query(params=paramsQuery)
    
    if len(result.result["data"]["messages"]) > 0:
        return result.result["data"]["messages"][0]
    else:
        return ""

def getTransactionGraphQL(tonClient: TonClient, messageID, fields):

    paramsQuery = ParamsOfQuery(query="query($msg: String){transactions(filter:{in_msg:{eq:$msg}}){" + fields + "}}", variables={"msg": messageID})
    result      = tonClient.net.query(params=paramsQuery)

    if len(result.result["data"]["transactions"]) > 0:
        return result.result["data"]["transactions"][0]
    else:
        return ""

def getExitCodeFromMessageID(tonClient: TonClient, messageID, fields):
    result       = getTransactionGraphQL(tonClient, messageID, fields)
    realExitCode = result["compute"]["exit_code"]
    return realExitCode

# ==============================================================================
#
def _unwrapMessages(tonClient: TonClient, messageID, parentMessageID, abiFilesArray):

    #messageFilters     = "id, src, dst, body, dst_transaction{id}, value(format:DEC), ihr_fee(format:DEC), import_fee(format:DEC), fwd_fee(format:DEC)"
    # TODO: temporary fix, to exclude EVENT from calculations for now
    messageFilters     = "id, src, dst, body, value(format:DEC), ihr_fee(format:DEC), import_fee(format:DEC), fwd_fee(format:DEC)"
    messageFiltersFix  = "id, src, dst, body, dst_transaction{id}, value(format:DEC), ihr_fee(format:DEC), import_fee(format:DEC), fwd_fee(format:DEC)"
    transactionFilters = "status, status_name, end_status, out_msgs, outmsg_cnt, aborted, compute{exit_arg, exit_code, skipped_reason, skipped_reason_name, gas_fees(format:DEC)}, total_fees(format:DEC), storage{storage_fees_collected(format:DEC)}"

    resultMsg = getMessageGraphQL(tonClient, messageID, messageFilters)
    if resultMsg == "":
        return []
    (abi, resultMessageBody) = decodeMessageBody(resultMsg["body"], abiFilesArray)

    # TODO: temporary fix, to exclude EVENT from calculations for now
    if (resultMessageBody != "" and resultMessageBody.body_type != "Event") or resultMessageBody == "":
        resultMsg = getMessageGraphQL(tonClient, messageID, messageFiltersFix)

    # Loop while we are waiting for all results
    resultTransaction = ""
    while True:
        if resultMsg["dst"] == "":
            break
        if resultMsg["dst_transaction"] is None:
            break
        if resultMsg["dst_transaction"]["id"] is None:
            break
        resultTransaction = getTransactionGraphQL(tonClient, messageID, transactionFilters)
        if resultTransaction != "":
            break
        else:
            time.sleep(1)

    arrayMsg = [{
        "SOURCE":             resultMsg["src"],
        "DEST":               resultMsg["dst"] if resultMsg["dst"] != "" else "---",
        "VALUE":              resultMsg["value"],
        "FEES":               {"ihr_fee":resultMsg["ihr_fee"], "import_fee":resultMsg["import_fee"], "fwd_fee":resultMsg["fwd_fee"]},
        "MESSAGE_ID:":        messageID,
        "PARENT_MESSAGE_ID:": parentMessageID,
        "TARGET_ABI":         abi,
        "CALL_TYPE":          resultMessageBody.body_type     if resultMessageBody != "" else "---",
        "FUNCTION_NAME":      resultMessageBody.name          if resultMessageBody != "" else "---",
        "FUNCTION_PARAMS":    resultMessageBody.value         if resultMessageBody != "" else "---",
        "MSG_HEADER":         resultMessageBody.header        if resultMessageBody != "" else "---",
        "OUT_MSGS":           resultTransaction["out_msgs"]   if resultTransaction != "" else [],
        "OUT_MSG_CNT":        resultTransaction["outmsg_cnt"] if resultTransaction != "" else 0,
        "TX_DETAILS":         resultTransaction               if resultTransaction != "" else "---"
    }]

    if resultTransaction != "":
        for msg in resultTransaction["out_msgs"]:
            arrayResult = _unwrapMessages(tonClient, msg, messageID, abiFilesArray)
            arrayMsg   += arrayResult
    
    return arrayMsg

def unwrapMessages(tonClient: TonClient, messageIdArray, abiFilesArray):
    arrayMsg = []
    for msg in messageIdArray:
        arrayResult = _unwrapMessages(tonClient, msg, "", abiFilesArray)
        arrayMsg   += arrayResult
    
    return arrayMsg

# ==============================================================================
#
class SetcodeMultisig(object):
    def __init__(self, tonClient: TonClient, signer: Signer = None):
        self.SIGNER      = generateSigner() if signer is None else signer
        self.TONCLIENT   = tonClient
        self.ABI         = "../bin/SetcodeMultisigWallet.abi.json"
        self.TVC         = "../bin/SetcodeMultisigWallet.tvc"
        self.CONSTRUCTOR = {"owners":["0x" + self.SIGNER.keys.public],"reqConfirms":"1"}
        self.INITDATA    = {}
        self.PUBKEY      = self.SIGNER.keys.public
        self.ADDRESS     = getAddress(abiPath=self.ABI, tvcPath=self.TVC, signer=self.SIGNER, initialPubkey=self.SIGNER.keys.public, initialData=self.INITDATA)

    def deploy(self):
        result = deployContract(tonClient=self.TONCLIENT, abiPath=self.ABI, tvcPath=self.TVC, constructorInput=self.CONSTRUCTOR, initialData=self.INITDATA, signer=self.SIGNER, initialPubkey=self.PUBKEY)
        return result

    def call(self, functionName, functionParams):
        result = callFunction(tonClient=self.TONCLIENT, abiPath=self.ABI, contractAddress=self.ADDRESS, functionName=functionName, functionParams=functionParams, signer=self.SIGNER)
        return result

    def callTransfer(self, addressDest, value, payload, flags):
        result = self.call(functionName="sendTransaction", functionParams={"dest":addressDest, "value":value, "bounce":False, "flags":flags, "payload":payload})
        return result

    def run(self, functionName, functionParams):
        result = runFunction(tonClient=self.TONCLIENT, abiPath=self.ABI, contractAddress=self.ADDRESS, functionName=functionName, functionParams=functionParams)
        return result

    def destroy(self, addressDest):
        result = callFunction(tonClient=self.TONCLIENT, abiPath=self.ABI, contractAddress=self.ADDRESS, functionName="sendTransaction", functionParams={"dest":addressDest, "value":0, "bounce":False, "flags":128+32, "payload":""}, signer=self.SIGNER)
        return result

# ==============================================================================
#
def giverGetAddress():

    global MSIG_GIVER

    if MSIG_GIVER == "":
        return "0:841288ed3b55d9cdafa806807f02a0ae0c169aa5edfe88a789a6482429756a94"
    else:
        signer = loadSigner(MSIG_GIVER)
        msig   = SetcodeMultisig(tonClient=TonClient(config=ClientConfig()), signer=signer)
        return msig.ADDRESS

def giverGive(tonClient: TonClient, contractAddress, amountTons):
    
    if not USE_GIVER:
        print("\nNow GIVER expects to give {} TONs to address {};".format(amountTons, contractAddress))
        input("Please, do it manually and then press ENTER to continue...")
        return

    global MSIG_GIVER
    if MSIG_GIVER == "":
        giverAddress = giverGetAddress()
        callFunction(tonClient, "../bin/local_giver.abi.json", giverAddress, "sendGrams", {"dest":contractAddress,"amount":amountTons}, Signer.NoSigner())
    else:
        signer = loadSigner(MSIG_GIVER)
        msig   = SetcodeMultisig(signer=signer)
        msig.callTransfer(addressDest=contractAddress, value=amountTons, payload="", flags=1)

# ==============================================================================
#
