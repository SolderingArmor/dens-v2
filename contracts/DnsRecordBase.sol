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
    
    uint32  constant MAX_SEGMENTS_NUMBER   = 4;
    uint32  constant MAX_SEPARATORS_NUMBER = (MAX_SEGMENTS_NUMBER - 1);
    uint32  constant MIN_SEGMENTS_LENGTH   = 2;
    uint32  constant MAX_SEGMENTS_LENGTH   = 31;
    uint32  constant MAX_DOMAIN_LENGTH     = MAX_SEGMENTS_NUMBER * MAX_SEGMENTS_LENGTH + MAX_SEPARATORS_NUMBER;

    //========================================
    // Error codes
    uint constant ERROR_MESSAGE_SENDER_IS_NOT_MY_OWNER      = 100;
    uint constant ERROR_MESSAGE_SENDER_IS_NOT_MY_ROOT       = 101;
    uint constant ERROR_EITHER_ADDRESS_OR_PUBKEY            = 102;
    uint constant ERROR_REQUIRE_INTERNAL_MESSAGE_WITH_VALUE = 103;
    uint constant ERROR_DOMAIN_NAME_NOT_VALID               = 200;
    uint constant ERROR_DOMAIN_IS_EXPIRED                   = 201;
    uint constant ERROR_DOMAIN_IS_NOT_EXPIRED               = 202;
    uint constant ERROR_DOMAIN_IS_PENDING                   = 203;
    uint constant ERROR_DOMAIN_IS_NOT_PENDING               = 204;
    uint constant ERROR_CAN_NOT_PROLONGATE_YET              = 205;
    uint constant ERROR_WRONG_REGISTRATION_TYPE             = 206;
    uint constant ERROR_DOMAIN_REG_REQUEST_DOES_NOT_EXIST   = 207;
    uint constant ERROR_DOMAIN_REG_REQUEST_ALREADY_EXISTS   = 208;
    uint constant ERROR_MESSAGE_SENDER_IS_NOT_MY_SUBDOMAIN  = 209;
    uint constant ERROR_MESSAGE_SENDER_IS_NOT_VALID         = 210;
    
    //========================================
    // Variables
    string   internal static _domainName;
    bool     internal        _nameIsValid;
    TvmCell  internal static _domainCode;
    DnsWhois internal        _whoisInfo;

    //========================================
    // Getters
    function callWhois()   external view responsible override returns (DnsWhois  ) {    return{value: 0, flag: 64}(_whoisInfo);         }
    function getWhois()                external view override returns (DnsWhois  ) {    return _whoisInfo;                              }
    //
    function getDomainName()           external view override returns (string    ) {    return _whoisInfo.domainName;                   }
    function getDomainCode()           external view override returns (TvmCell   ) {    return _domainCode;                             }
    //
    function getEndpointAddress()      external view override returns (address   ) {    return _whoisInfo.endpointAddress;              }
    function getSegmentsCount()        external view override returns (uint8     ) {    return _whoisInfo.segmentsCount;                }
    function getParentDomainName()     external view override returns (string    ) {    return _whoisInfo.parentDomainName;             }
    function getParentDomainAddress()  external view override returns (address   ) {    return _whoisInfo.parentDomainAddress;          }    
    //
    function getOwnerID()              external view override returns (uint256   ) {    return _whoisInfo.ownerID;                      }
    function getDtLastProlongation()   external view override returns (uint32    ) {    return _whoisInfo.dtLastProlongation;           }
    function getDtExpires()            external view override returns (uint32    ) {    return _whoisInfo.dtExpires;                    }
    function getSubdomainRegPrice()    external view override returns (uint128   ) {    return _whoisInfo.subdomainRegPrice;            }
    function getRegistrationType()     external view override returns (REG_TYPE  ) {    return _whoisInfo.registrationType;             }
    function getLastRegResult()        external view override returns (REG_RESULT) {    return _whoisInfo.lastRegResult;                }
    function getComment()              external view override returns (string    ) {    return _whoisInfo.comment;                      }
    //
    function getDtCreated()            external view override returns (uint32    ) {    return _whoisInfo.dtCreated;                    }
    function getTotalOwnersNum()       external view override returns (uint32    ) {    return _whoisInfo.totalOwnersNum;               }
    function getSubdomainRegAccepted() external view override returns (uint32    ) {    return _whoisInfo.subdomainRegAccepted;         }
    function getSubdomainRegDenied()   external view override returns (uint32    ) {    return _whoisInfo.subdomainRegDenied;           }
    function getTotalFeesCollected()   external view override returns (uint128   ) {    return _whoisInfo.totalFeesCollected;           }
    //
    function canProlongate()           public   view override returns (bool      ) {    return (now <= _whoisInfo.dtExpires && 
                                                                                                now >= _whoisInfo.dtExpires - tenDays); }
    function isExpired()               public   view override returns (bool      ) {    return  now >  _whoisInfo.dtExpires;            }

    //========================================
    //
    function withdrawBalance(uint128 amount, address dest) external override onlyOwner notExpired
    {
        if(msg.pubkey() != 0) { tvm.accept(); }

        dest.transfer(amount, false, 1);

        if(msg.value > 0) { msg.sender.transfer(0, true, 64); }
    }
    
    //========================================
    //
    function changeEndpointAddress(address newAddress) external override onlyOwner notExpired
    {
        if(msg.pubkey() != 0) { tvm.accept(); }

        _whoisInfo.endpointAddress = newAddress;

        if(msg.value > 0) { msg.sender.transfer(0, true, 64); }
    }

    //========================================
    //
    function changeRegistrationType(REG_TYPE newType) external override onlyOwner notExpired
    {
        require(newType < REG_TYPE.NUM, ERROR_WRONG_REGISTRATION_TYPE);        
        if(msg.pubkey() != 0) { tvm.accept(); }

        _whoisInfo.registrationType = newType;

        if(msg.value > 0) { msg.sender.transfer(0, true, 64); }
    }

    //========================================
    //
    function changeComment(string newComment) external override onlyOwner notExpired
    {
        if(msg.pubkey() != 0) { tvm.accept(); }

        _whoisInfo.comment = newComment;

        if(msg.value > 0) { msg.sender.transfer(0, true, 64); }
    }

    //========================================
    //
    function changeSubdomainRegPrice(uint128 price) external override onlyOwner notExpired
    {
        if(msg.pubkey() != 0) { tvm.accept(); }

        _whoisInfo.subdomainRegPrice = price;

        if(msg.value > 0) { msg.sender.transfer(0, true, 64); }
    }

    //========================================
    //
    function _changeOwner(uint256 newOwnerID) internal
    {
        _whoisInfo.ownerID          = newOwnerID;
        _whoisInfo.endpointAddress  = addressZero;
        _whoisInfo.registrationType = REG_TYPE.DENY; // prevent unwanted subdomains from registering by accident right after domain modification;
        _whoisInfo.comment          = "";
    }

    function changeOwner(uint256 newOwnerID) external override onlyOwner notExpired
    {
        if(msg.pubkey() != 0) { tvm.accept(); }

        // Increase counter only if new owner is different
        if(newOwnerID != _whoisInfo.ownerID)
        {
            _whoisInfo.totalOwnersNum += 1;
        }

        _changeOwner(newOwnerID);

        if(msg.value > 0) { msg.sender.transfer(0, true, 64); }
    }

    //========================================
    //
    function prolongate() external override onlyOwner notExpired
    {
        require(canProlongate(), ERROR_CAN_NOT_PROLONGATE_YET);
        
        if(msg.pubkey() != 0) { tvm.accept(); }

        _whoisInfo.dtExpires += ninetyDays;

        if(msg.value > 0) { msg.sender.transfer(0, true, 64); }
    }

    //========================================
    /// @notice Split the string using "/" as a separator;
    /// @dev    We purposely use "byteLength()" because we know that all letters will be in a range of a single byte;
    ///
    /// @param stringToSplit - string to split;
    ///
    /// @return string[]: string array (segments);
    //
    function splitString(string stringToSplit) internal pure returns(string[]) 
    {
        require(stringToSplit.byteLength() >= MIN_SEGMENTS_LENGTH && stringToSplit.byteLength() <= MAX_DOMAIN_LENGTH, ERROR_DOMAIN_NAME_NOT_VALID);
        
        bytes stringToSplitBytes = bytes(stringToSplit);
        string[] finalWordsArray;        
        
        uint lastPos = 0;
        for(uint i = 0; i < stringToSplitBytes.length; i++) 
        {
            byte letter = stringToSplitBytes[i];
            if(letter == 0x2F) // slash
            {
                if(i - lastPos > 0) // don't add empty strings; we ignore errors here because "_validateDomainName" will take care of it;
                {
                    finalWordsArray.push(stringToSplit.substr(lastPos, i - lastPos));
                }
                lastPos = i + 1;
            }
        }

        // Add last word
        if(stringToSplitBytes.length - lastPos > 0)
        {
            finalWordsArray.push(stringToSplit.substr(lastPos, stringToSplitBytes.length - lastPos - 1));
        }

        return finalWordsArray;
    }

    //========================================
    /// @notice Validate domain segment length;
    ///
    /// @param length - segment length without separators;
    ///
    /// @return bool: if length is valid or not;
    //
    function _validateSegmentLength(uint32 length) internal inline pure returns (bool)
    {
        // segment too short or too long, or two "/" in a row, error;
        return (length >= MIN_SEGMENTS_LENGTH && length <= MAX_SEGMENTS_LENGTH);
    }

    //========================================
    /// @notice Validate domain name;
    ///
    /// @param domainName - domain name; can include lowercase letters, numbers and "/";
    ///
    /// @return bool: if the name is valid or not;
    //
    function _validateDomainName(bytes domainName) internal pure returns (bool)
    {
        if(domainName.length < MIN_SEGMENTS_LENGTH || domainName.length > MAX_DOMAIN_LENGTH)
        {
            return false;
        }

        uint32 separatorCount   = 0;
        uint32 lastSeparatorPos = 0;

        for(uint32 i = 0; i < domainName.length; i++)
        {
            byte  letter  = domainName[i];
            bool  numbers = (letter >= 0x30 && letter <= 0x39);
            bool  lower   = (letter >= 0x61 && letter <= 0x7A);
            bool  dash    = (letter == 0x2D);
            bool  slash   = (letter == 0x2F);

            if(!numbers && !lower && !dash && !slash)
            {
                return false;
            }

            if(slash)
            {
                separatorCount += 1;
                uint32 len = i - lastSeparatorPos;
                
                // One symbol in this length is separator itself, get rid of it (only if we had one or more separators already);
                uint32 extraSlash = (lastSeparatorPos == 0 ? 0 : 1);
                if(len == 0 || !_validateSegmentLength(len - extraSlash)) {    return false;    }

                lastSeparatorPos = i;
            }
        }

        // last segment has no separator at the end, duplicate the check
        uint32 extraSlash = (lastSeparatorPos == 0 ? 0 : 1);
        uint32 len        = uint32(domainName.length) - lastSeparatorPos - extraSlash;
        if(!_validateSegmentLength(len)) {    return false;    }

        if(separatorCount > MAX_SEPARATORS_NUMBER)
        {
            return false;
        }

        return true;
    }

    //========================================
    /// @notice Parse domain name and extract segments and parent domain name; 
    ///         Don't forget to validate domain first (if needed)!
    ///
    /// @param domainName - domain name;
    ///
    /// @return string[]: parsed domain name (segments);
    ///         string:   parent domain name;
    //
    function _parseDomainName(string domainName) internal pure returns (string[], string)
    {
        // Parse to segments
        string[] segments = splitString(domainName);
        if(segments.length == 0)
        {
            return(segments, "");
        }
        
        uint32 lastSegmentName = segments[segments.length-1].byteLength();
        uint32 parentLength    = domainName.byteLength() - lastSegmentName - 1;
        string parentName      = (segments.length == 1 ? domainName : domainName.substr(0, parentLength - 1));

        return (segments, parentName);
    }

    //========================================
    // Modifiers
    modifier onlyOwner
    {
        // Owner can make changes only after registration process is completed;
        bool byPubKey  = (_whoisInfo.ownerID == msg.pubkey()     && msg.pubkey() != 0          );
        bool byAddress = (_whoisInfo.ownerID == msg.sender.value && msg.sender   != addressZero);

        require(byPubKey || byAddress, ERROR_MESSAGE_SENDER_IS_NOT_MY_OWNER);
        _;
    }

    modifier onlyRoot
    {
        require(_whoisInfo.parentDomainAddress == msg.sender, ERROR_MESSAGE_SENDER_IS_NOT_MY_ROOT);
        _;
    }

    modifier notExpired
    {
        require(!isExpired(), ERROR_DOMAIN_IS_EXPIRED);
        _;
    }

    modifier Expired
    {
        require(isExpired(), ERROR_DOMAIN_IS_NOT_EXPIRED);
        _;
    }

    modifier NameIsValid
    {
        require(_nameIsValid, ERROR_DOMAIN_NAME_NOT_VALID);
        _;
    }
}

//================================================================================
//