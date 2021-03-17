pragma ton-solidity >= 0.38.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
struct DnsWhois
{
    address endpointAddress;     //
    //
    uint8   segmentsCount;       //
    bytes   parentDomainName;    //
    address parentDomainAddress; //
    //
    address ownerAddress;        //
    uint256 ownerPubkey;         //
    uint32  dtLastProlongation;  //
    uint32  dtExpires;           //
    uint128 subdomainRegPrice;   // 
    bytes   comment;             //
    //
    // Statistics
    uint32  dtCreated;
    uint32  totalOwnersNum;      // Total owners number, increases when expired domain is claimed;
    uint32  subdomainRegCount;   // Total number of sub-domains registered;
    uint128 totalFeesCollected;  // Total fees collected registering subdomains;

}

//================================================================================
//
interface IDnsRecord
{
    //========================================
    // Getters
    function getWhois()               external view returns (DnsWhois);
    //
    function getDomainName()          external view returns (bytes   );
    function getDomainCode()          external view returns (TvmCell );
    function getSegmentsCount()       external view returns (uint8   );
    function getParentDomainName()    external view returns (bytes   );
    function getParentDomainAddress() external view returns (address );    
    //
    function getOwnerAddress()        external view returns (address );
    function getOwnerPubkey()         external view returns (uint256 );
    function getDtLastProlongation()  external view returns (uint32  );
    function getDtExpires()           external view returns (uint32  );
    function getSubdomainRegPrice()   external view returns (uint128 );
    function getComment()             external view returns (bytes   );
    //
    function getDtCreated()           external view returns (uint32  );
    function getTotalOwnersNum()      external view returns (uint32  );
    function getSubdomainRegCount()   external view returns (uint32  );
    function getTotalFeesCollected()  external view returns (uint128 );
    //
    function canProlongate()          external view returns (bool    );

    //========================================
    //
    function calculateFutureAddress(bytes domainName) external view returns (address, TvmCell);
}

//================================================================================
//