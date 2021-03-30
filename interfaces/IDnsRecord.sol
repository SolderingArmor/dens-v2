pragma ton-solidity >= 0.38.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
enum REG_TYPE
{
    FFA,     // Free For All, anyone can register a subdomain;
    MONEY,   // Registration is like FFA BUT you need to attach enough money (configurable by parent domain);
    OWNER,   // Only owner can register a subdomain, all other request are denied;
    DENY,    // All requests are denied;
    NUM
}

enum REG_RESULT
{
    NONE,             // 
    APPROVED,         // Cool;
    DENIED,           // Root domain denies the registration (either automatically or manually), try again later;
    NOT_ENOUGH_MONEY, // Root domain requires more money to send;
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
    uint256    ownerID;             //
    uint32     dtLastProlongation;  //
    uint32     dtExpires;           //
    uint128    subdomainRegPrice;   // 
    REG_TYPE   registrationType;    //
    REG_RESULT lastRegResult;       //
    string     comment;             //
    //
    // Statistics
    uint32     dtCreated;            //
    uint32     totalOwnersNum;       // Total owners number, increases when expired domain is claimed;
    uint32     subdomainRegAccepted; // Total number of sub-domains registerations accepted;
    uint32     subdomainRegDenied;   // Total number of sub-domains registerations denied;
    uint128    totalFeesCollected;   // Total fees collected registering subdomains;
    
}

//================================================================================
//
interface IDnsRecord
{
    //========================================
    // Events
    event newSubdomainRegistered(uint32 dt, string domainName, uint128 price  );
    event registrationResult    (uint32 dt, REG_RESULT result, uint256 ownerID);
    event domainReleased        (uint32 dt);

    //========================================
    // Getters
    function callWhois()   external view responsible returns (DnsWhois  );
    function getWhois()                external view returns (DnsWhois  );
    //
    function getDomainName()           external view returns (string    );
    function getDomainCode()           external view returns (TvmCell   );
    //
    function getEndpointAddress()      external view returns (address   );
    function getSegmentsCount()        external view returns (uint8     );
    function getParentDomainName()     external view returns (string    );
    function getParentDomainAddress()  external view returns (address   );    
    //
    function getOwnerID()              external view returns (uint256   );
    function getDtLastProlongation()   external view returns (uint32    );
    function getDtExpires()            external view returns (uint32    );
    function getSubdomainRegPrice()    external view returns (uint128   );
    function getRegistrationType()     external view returns (REG_TYPE  );
    function getLastRegResult()        external view returns (REG_RESULT);
    function getComment()              external view returns (string    );
    //
    function getDtCreated()            external view returns (uint32    );
    function getTotalOwnersNum()       external view returns (uint32    );
    function getSubdomainRegAccepted() external view returns (uint32    );
    function getSubdomainRegDenied()   external view returns (uint32    );
    function getTotalFeesCollected()   external view returns (uint128   );
    //
    function canProlongate()           external view returns (bool      );
    function isExpired()               external view returns (bool      );
    //

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
    ///         Resets some DNS values like endpointAddress and comment;
    ///
    /// @param newOwnerID  - address or pubkey  of a new owner; can be (0, 0);
    ///
    /// @dev If you set both newOwnerAddress and newOwnerPubkey to 0, you will loose ownership of the domain!
    //
    function changeOwnership(uint256 newOwnerID) external;
    
    /// @notice Change sub-domain registration type;
    ///
    /// @param newType - new type;
    //
    function changeRegistrationType(REG_TYPE newType) external;

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
    /// @param newOwnerID    - address or pubkey  of a new owner; can be (0, 0);
    /// @param tonsToInclude - TONs to include in message value; TONs need to come with inbound message, it should be enough to pay for domain registration and for all gas fees;
    //
    function claimExpired(uint256 newOwnerID, uint128 tonsToInclude) external;
    
    /// @notice Release a domain, owner becomes no one, dtExpires becomes 0;
    //
    function releaseDomain() external;

    /// @notice Receive registration request from a sub-domain;
    ///
    /// @param domainName - sub-domain name;
    /// @param ownerID    - address or pubkey  of a new owner;
    //
    function receiveRegistrationRequest(string domainName, uint256 ownerID, address payerAddress) external responsible returns (REG_RESULT, uint256, address);
    
    /// @notice Callback received from parent domain with registration result;
    ///
    /// @param result - registration result;
    //
    function callbackOnRegistrationRequest(REG_RESULT result, uint256 ownerID, address payerAddress) external;

    //========================================
    // Sub-domain management

    /// @notice Change sub-domain registration price;
    ///
    /// @param price - new registration price;
    //
    function changeSubdomainRegPrice(uint128 price) external;
    
    //========================================
    // Misc

    /// @notice Withdraw some balance;
    ///
    /// @param amount - amount in nanotons;
    /// @param dest   - money destination;
    //
    function withdrawBalance(uint128 amount, address dest) external;

}

//================================================================================
//