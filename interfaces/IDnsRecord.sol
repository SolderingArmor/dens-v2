pragma ton-solidity >= 0.38.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
struct DnsWhois
{
    bytes   domainName;           //
    bytes   parentDomainName;     //
    address parentDomainAddress;  //
    
    address ownerAddress;         //
    uint256 ownerPubkey;          //
    uint64  lastProlongationDate; //
    uint64  expiresAt;            //
    uint128 subdomainRegPrice;    // 
    bytes   comment;              //

    // Statistics
    uint64  dtCreated;
    uint32  totalOwners;          // Total owners number, increases when expired domain is claimed;
    uint32  subdomainRegCount;    // Total number of sub-domains registered;
    uint128 totalFeesCollected;   // Total fees collected registering subdomains;

}

//================================================================================
//
interface IDnsRecord
{
    //========================================
    // Getters
    function getWhois()                external view returns (DnsWhois);
    //
    function getDomainName()           external view returns (bytes   );
    function getParentDomainName()     external view returns (bytes   );
    function getParentDomainAddress()  external view returns (address );    
    //
    function getOwnerAddress()         external view returns (address );
    function getOwnerPubkey()          external view returns (uint256 );
    function getLastProlongationDate() external view returns (uint64  );
    function getExpiresAt()            external view returns (uint64  );
    function getSubdomainRegPrice()    external view returns (uint128 );
    function getComment()              external view returns (bytes   );
    //
    function getDtCreated()            external view returns (uint64  );
    function getTotalOwners()          external view returns (uint32  );
    function getSubdomainRegCount()    external view returns (uint32  );
    function getTotalFeesCollected()   external view returns (uint128 );
    //
    function canProlongate()           external view returns (bool    );
}

//================================================================================
//