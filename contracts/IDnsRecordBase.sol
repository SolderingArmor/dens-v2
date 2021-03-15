pragma ton-solidity >= 0.38.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
import "../interfaces/IDnsRecord.sol";

//================================================================================
//
abstract contract IDnsRecordBase is IDnsRecord
{
    //========================================
    // Error codes
    uint constant ERROR_MESSAGE_SENDER_IS_NOT_MY_OWNER = 100;
    uint constant ERROR_MESSAGE_SENDER_IS_NOT_MY_ROOT  = 101;
    uint constant ERROR_EITHER_ADDRESS_OR_PUBKEY       = 102;
    
    //========================================
    // Common functions
    function splitString(string stringToSplit) internal pure returns(bytes[]) 
    {
        bytes[] finalWordsArray;
        bytes stringAsBytesArray = bytes(stringToSplit);
        
        uint lastPos = 0;
        for(uint i = 0; i < stringAsBytesArray.length; i++) 
        {
            if(stringAsBytesArray[i] == "/")
            {
                if(i - lastPos > 0) // don't add empty strings
                {
                    finalWordsArray.push(stringToSplit.substr(lastPos, i - lastPos));
                }
                lastPos = i + 1;
            }
        }

        // Add last word
        if(stringAsBytesArray.length - lastPos > 0)
        {
            finalWordsArray.push(stringToSplit.substr(lastPos, stringAsBytesArray.length - lastPos));
        }

        return finalWordsArray;
    }
    
    //========================================
    //
    function _parseDnsName(string dnsName) internal returns (bytes, uint8)
    {
        bytes bytesName = bytes(dnsName);
        require(bytesName.length > 1, 5555);

        // 1. Check for illegal symbols
        for(uint256 i = 0; i < bytesName.length; i++)
        {
            bool numbers = (bytesName[i] >= 0x30 && bytesName[i] <= 0x39);
            bool lower   = (bytesName[i] >= 0x61 && bytesName[i] <= 0x7A);
            bool slash   = (bytesName[i] == 0x2F);

            if(!numbers && !lower && !slash)
            {
                require(false, 5556);
            }
        }

        // 2. Parse to segments
        bytes[] segments = splitString(dnsName);
        bytes parentName = (segments.length == 1 ? bytesName : bytes(dnsName.substr(0, bytesName.length - segments[segments.length-1].length)));

        // ...
        return (parentName, uint8(segments.length));
    }

    //========================================
    //
    
}

//================================================================================
//