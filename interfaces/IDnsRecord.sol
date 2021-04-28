pragma ton-solidity >= 0.42.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
enum REG_TYPE
{
    FFA,     // Free For All, anyone can register a subdomain;
    MONEY,   // Registration is like FFA BUT you need to attach enough money (configurable by parent domain);
    OWNER,   // Only owner can register a subdomain (thus be an owner of a subdomain, unless he transfers ownership manually), all other request are denied;
    DENY,    // All requests are denied;
    NUM
}

enum REG_RESULT
{
    NONE,             // 
    APPROVED,         // Cool;
    DENIED,           // Root domain denies the registration, fulfill registration requirements and try again;
    NOT_ENOUGH_MONEY, // Not enough money attached to "claimExpired" message;
    NUM
}

//================================================================================
// 
struct DnsWhois
{
    address    endpointAddress;     //
    //
    uint8      segmentsCount;       //
    string     domainName;          // duplicating domain name here; we can't use pointers, but it needs to be a part of Whois;
    string     parentDomainName;    //
    address    parentDomainAddress; //
    //
    address    ownerAddress;        //
    uint32     dtLastProlongation;  //
    uint32     dtExpires;           //
    uint128    registrationPrice;   // 
    REG_TYPE   registrationType;    //
    REG_RESULT lastRegResult;       //
    string     comment;             //
    //
    // Statistics
    uint32     dtCreated;            //
    uint128    totalOwnersNum;       // Total owners number, increases when expired domain is claimed;
    uint128    subdomainRegAccepted; // Total number of sub-domains registerations accepted;
    uint128    subdomainRegDenied;   // Total number of sub-domains registerations denied;
    uint128    totalFeesCollected;   // Total fees collected registering subdomains;
    
}

//================================================================================
//
interface IDnsRecord
{
    //========================================
    // Events
    event newSubdomainRegistered(uint32 dt, string domainName, uint128 price       );
    event registrationResult    (uint32 dt, REG_RESULT result, address ownerAddress);
    event ownerChanged          (uint32 dt, address oldOwner, address newOwner);
    event domainProlongated     (uint32 dt, uint32 expirationDate);
    event domainReleased        (uint32 dt);

    //========================================
    // Getters
    function getDomainCode() external view returns (TvmCell);
    function canProlongate() external view returns (bool   );
    function isExpired()     external view returns (bool   );
    //
    function callWhois()           external view responsible returns (DnsWhois);
    function getWhois()                        external view returns (DnsWhois);
    function callEndpointAddress() external view responsible returns (address );
    function  getEndpointAddress() external view             returns (address );

    //========================================
    //
    function calculateDomainAddress(string domainName) external view returns (address, TvmCell);

    //========================================
    // Sets
    /// @notice Change the endpoint address that DeNS record keeps;
    ///
    /// @param newAddress - new target address of this DeNS;
    //
    function changeEndpointAddress(address newAddress) external;
    
    /// @notice Change the owner;
    ///         Resets some DNS values like endpointAddress, registrationType, comment, etc.;
    ///
    /// @param newOwnerAddress - address of a new owner; can't be zero;
    //
    function changeOwner(address newOwnerAddress) external;
    
    /// @notice Change sub-domain registration type;
    ///
    /// @param newType - new type;
    //
    function changeRegistrationType(REG_TYPE newType) external;

    /// @notice Change sub-domain registration price;
    ///
    /// @param newPrice - new price;
    //
    function changeRegistrationPrice(uint128 newPrice) external;

    /// @notice Change comment;
    ///         Keep in mind that you will have to pay larger storage fees for huge comments;
    ///
    /// @param newComment - new comment;
    //
    function changeComment(string newComment) external;

    //========================================
    // Registration

    /// @notice Prolongate the domain; only owner can call this and only 10 or less days prior to expiration;
    //
    function prolongate() external;
    
    /// @notice Claim an expired DeNS Record; claiming is the same as registering new domain, except you don't deploy;
    ///
    /// @dev If REG_TYPE == REG_TYPE.MONEY on parent, all extra TONs (from msg.value) that exceed registration price will BE RETURNED to caller's account;
    ///      Plan accordingly: "msg.value" should equal to:
    ///      registration price (is 0 if REG_TYPE != MONEY) + all child fees (equivalent of 100'000 gas, or 0.1 TON should be enough) + all parent fees (equivalent of 300'000 gas, or 0.3 TON should be enough);
    ///      Long story short: extra 0.5 TON will cover everything, the change will be sent back;
    ///
    /// @param newOwnerAddress       - address or pubkey  of a new owner; can be 0;
    /// @param forceFeeReturnToOwner - sedns registration fees change not to "msg.sender", but to "ownerAddress"; mandatory for DeBot deployment, optional for all other ways of deployment;
    //
    function claimExpired(address newOwnerAddress, bool forceFeeReturnToOwner) external;
    
    /// @notice Release a domain, owner becomes no one, dtExpires becomes 0;
    //
    function releaseDomain() external;

    /// @notice Receive registration request from a sub-domain;
    ///
    /// @param domainName   - sub-domain name;
    /// @param ownerAddress - address of a new owner;
    /// @param payerAddress - address of a Multisig/payer contract;
    //
    function receiveRegistrationRequest(string domainName, address ownerAddress, address payerAddress) external responsible returns (REG_RESULT, address, address);
    
    /// @notice Callback received from parent domain with registration result;
    ///
    /// @param result       - registration result;
    /// @param ownerAddress - address of a new owner;
    /// @param payerAddress - address of a Multisig/payer contract;
    //
    function callbackOnRegistrationRequest(REG_RESULT result, address ownerAddress, address payerAddress) external;
}

//================================================================================
//
abstract contract DnsFunctionsCommon
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
    uint constant ERROR_REQUIRE_INTERNAL_MESSAGE_WITH_VALUE = 102;
    uint constant ERROR_WORKCHAIN_NEEDS_TO_BE_0             = 103;
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
    uint constant ERROR_NOT_ENOUGH_MONEY                    = 211;
    uint constant ERROR_ADDRESS_CAN_NOT_BE_EMPTY            = 212;
    uint constant ERROR_CAN_NOT_TRANSFER_TO_YOURSELF        = 213;
    
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
        
        uint32 lastSegmentName = uint32(segments[segments.length-1].byteLength());
        uint32 parentLength    = uint32(domainName.byteLength()) - lastSegmentName - 1;
        string parentName      = (segments.length == 1 ? domainName : domainName.substr(0, parentLength - 1));

        return (segments, parentName);
    }
}


//================================================================================
//