pragma ton-solidity >= 0.38.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
import "../interfaces/IDnsRecord.sol";

//================================================================================
//
abstract contract DnsRecordBase is IDnsRecord
{
    //========================================
    // Constants
    address constant addressZero = address.makeAddrStd(0, 0); //
    uint32  constant tenDays     = 60 * 60 * 24 * 10;         // 10 days in seconds
    uint32  constant ninetyDays  = tenDays * 9;               // 90 days in seconds
    
    //========================================
    // Error codes
    uint constant ERROR_MESSAGE_SENDER_IS_NOT_MY_OWNER = 100;
    uint constant ERROR_MESSAGE_SENDER_IS_NOT_MY_ROOT  = 101;
    uint constant ERROR_EITHER_ADDRESS_OR_PUBKEY       = 102;
    
    // Variables
    bytes    internal static _domainName;
    TvmCell  internal static _domainCode;
    DnsWhois internal        _whoisInfo;

    // Getters
    function getWhois()               external view override returns (DnsWhois) {    return _whoisInfo;                              }
    //
    function getDomainName()          external view override returns (bytes   ) {    return _domainName;                             }
    function getDomainCode()          external view override returns (TvmCell ) {    return _domainCode;                             }
    function getSegmentsCount()       external view override returns (uint8   ) {    return _whoisInfo.segmentsCount;                }
    function getParentDomainName()    external view override returns (bytes   ) {    return _whoisInfo.parentDomainName;             }
    function getParentDomainAddress() external view override returns (address ) {    return _whoisInfo.parentDomainAddress;          }    
    //
    function getOwnerAddress()        external view override returns (address ) {    return _whoisInfo.ownerAddress;                 }
    function getOwnerPubkey()         external view override returns (uint256 ) {    return _whoisInfo.ownerPubkey;                  }
    function getDtLastProlongation()  external view override returns (uint32  ) {    return _whoisInfo.dtLastProlongation;           }
    function getDtExpires()           external view override returns (uint32  ) {    return _whoisInfo.dtExpires;                    }
    function getSubdomainRegPrice()   external view override returns (uint128 ) {    return _whoisInfo.subdomainRegPrice;            }
    function getComment()             external view override returns (bytes   ) {    return _whoisInfo.comment;                      }
    //
    function getDtCreated()           external view override returns (uint32  ) {    return _whoisInfo.dtCreated;                    }
    function getTotalOwnersNum()      external view override returns (uint32  ) {    return _whoisInfo.totalOwnersNum;               }
    function getSubdomainRegCount()   external view override returns (uint32  ) {    return _whoisInfo.subdomainRegCount;            }
    function getTotalFeesCollected()  external view override returns (uint128 ) {    return _whoisInfo.totalFeesCollected;           }
    //
    function canProlongate()          external view override returns (bool    ) {    return (now <= _whoisInfo.dtExpires && 
                                                                                             now >= _whoisInfo.dtExpires - tenDays); }

    //========================================
    /// @notice 0000;
    ///
    /// @param stringToSplit - 0000;
    ///
    /// @return bytes[]: 0000;
    //
    function splitString(string stringToSplit) internal pure returns(bytes[]) 
    {
        bytes[] finalWordsArray;
        bytes stringBytes = bytes(stringToSplit);
        
        uint lastPos = 0;
        for(uint i = 0; i < stringBytes.length; i++) 
        {
            if(stringBytes[i] == "/")
            {
                if(i - lastPos > 0) // don't add empty strings
                {
                    finalWordsArray.push(stringToSplit.substr(lastPos, i - lastPos));
                }
                lastPos = i + 1;
            }
        }

        // Add last word
        if(stringBytes.length - lastPos > 0)
        {
            finalWordsArray.push(stringToSplit.substr(lastPos, stringBytes.length - lastPos - 1));
        }

        return finalWordsArray;
    }
    
    //========================================
    /// @notice 0000;
    ///
    /// @param domainName - domain name; can include lowercase letters, numbers and "/";
    ///
    /// @return bool: if the name is valid or not;
    //
    function _validateDomainName(bytes domainName) internal pure returns (bool)
    {
        require(domainName.length > 1, 5555);

        // TODO: do we need to check length and number of segments and empty segments?

        for(uint256 i = 0; i < domainName.length; i++)
        {
            bool numbers = (domainName[i] >= 0x30 && domainName[i] <= 0x39);
            bool lower   = (domainName[i] >= 0x61 && domainName[i] <= 0x7A);
            bool slash   = (domainName[i] == 0x2F);

            if(!numbers && !lower && !slash)
            {
                require(false, 5556);
            }
        }

        return true;
    }
    //========================================
    /// @notice Parse domain name and extract segments and parent domain name; 
    ///         don't forget to validate domain first!
    ///
    /// @param domainName - domain name;
    ///
    /// @return bytes[]: parsed domain name into segments;
    ///         bytes:   parent domain name;
    //
    function _parseDomainName(bytes domainName) internal pure returns (bytes[], bytes)
    {
        // TODO: do we need to spend gas here every time?
        require(_validateDomainName(domainName) == true, 5555);

        // Parse to segments
        bytes[] segments     = splitString(domainName);
        uint lastSegmentName = segments[segments.length-1].length;
        uint256 parentLength    = domainName.length - lastSegmentName - 1;
        //bytes parentName     = (segments.length == 1 ? bytesName : bytes(domainName.substr(0, bytesName.length - lastSegmentName - 1)));
        bytes parentName     = (segments.length == 1 ? domainName : bytes(domainName[0: parentLength]));

        // ...
        return (segments, parentName);
    }

    //========================================
    // Modifiers
    modifier onlyOwner
    {
        // Owner can make changes only after registration process is completed;
        bool byPubKey  = (_whoisInfo.ownerPubkey == msg.pubkey() && _whoisInfo.ownerAddress == addressZero);
        bool byAddress = (_whoisInfo.ownerPubkey == 0            && _whoisInfo.ownerAddress == msg.sender );

        require(byPubKey || byAddress, 7777);
        _;
    }

    modifier onlyRoot
    {
        require(_whoisInfo.parentDomainAddress == msg.sender, 7777);
        _;
    }    
}

//================================================================================
//