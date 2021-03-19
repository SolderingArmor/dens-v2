pragma ton-solidity >= 0.38.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
import "./DnsRecordBase.sol";

//================================================================================
//
contract DnsRecord is DnsRecordBase
{
    //========================================
    //
    /// @dev TODO: here "external" was purposely changed to "public", otherwise you get the following error:
    ///      Error: Undeclared identifier. "calculateFutureAddress" is not (or not yet) visible at this point.
    ///      The fix is coming: https://github.com/tonlabs/TON-Solidity-Compiler/issues/36
    function calculateDomainAddress(string domainName) public view override returns (address, TvmCell)
    {
        TvmCell stateInit = tvm.buildStateInit({
            contr: DnsRecord,
            varInit: {
                _domainName: domainName,
                _domainCode: _domainCode
            },
            code: _domainCode
        });

        return (address(tvm.hash(stateInit)), stateInit);
    }
    
    //========================================
    //
    constructor(address ownerAddress, uint256 ownerPubkey) public 
    {
        require(_validateDomainName(_domainName), 7777);

        tvm.accept();
        (bytes[] segments, bytes parentName) = _parseDomainName(_domainName);
        
        _whoisInfo.ownerAddress           = ownerAddress;
        _whoisInfo.ownerPubkey            = ownerPubkey;
        _whoisInfo.registrationType       = REG_TYPE.DENY; // prevent unwanted subdomains from registering by accident right after this domain registration;
        _whoisInfo.segmentsCount          = uint8(segments.length);
        _whoisInfo.parentDomainName       = parentName;
       (_whoisInfo.parentDomainAddress, ) = calculateDomainAddress(parentName);

        // if it is a ROOT domain name
        if(_whoisInfo.segmentsCount == 1) 
        {
            // Root domains won't need approval, internal callback right away
            _callbackOnRegistrationRequest(REG_RESULT.APPROVED);
        }
    }

    //========================================
    //
    function claimExpired(address newOwnerAddress, uint256 newOwnerPubkey) external override 
    {
        require(isExpired(), 6544);
        tvm.accept();

        _whoisInfo.ownerAddress     = newOwnerAddress;
        _whoisInfo.ownerPubkey      = newOwnerPubkey;
        _whoisInfo.endpointAddress  = addressZero;
        _whoisInfo.registrationType = REG_TYPE.DENY; // prevent unwanted subdomains from registering by accident right after this domain registration;
        _whoisInfo.comment          = "";
        _whoisInfo.totalOwnersNum  += 1;

        // if it is a ROOT domain name
        if(_whoisInfo.segmentsCount == 1) 
        {
            // Root domains won't need approval, internal callback right away
            _callbackOnRegistrationRequest(REG_RESULT.APPROVED);
        }
    }
    
    function sendRegistrationRequest(uint128 tonsToInclude) external override onlyOwner notExpired
    {
        uint128 tonsWithGas = gasToValue(10000, 0);
        IDnsRecord(_whoisInfo.parentDomainAddress).receiveRegistrationRequest{value: tonsWithGas, callback: IDnsRecord.callbackOnRegistrationRequest}(_domainName, _whoisInfo.ownerAddress, _whoisInfo.ownerPubkey);
    }
    
    function receiveRegistrationRequest(string domainName, address ownerAddress, uint256 ownerPubkey) external responsible override returns (REG_RESULT)
    {
        // TODO:
        // 1. Check if the request exists, fast and easy
        uint256 nameHash = tvm.hash(domainName);
        require(!_subdomainRegRequests.exists(nameHash), 6661); // already_exists

        // 2. Check if the request came from right domain
        (address addr, ) = calculateDomainAddress(domainName);
        require(addr == msg.sender, 6661);

        REG_RESULT result;
             if(_whoisInfo.registrationType == REG_TYPE.FFA)    {    result = REG_RESULT.APPROVED;    }
        else if(_whoisInfo.registrationType == REG_TYPE.DENY)   {    result = REG_RESULT.DENIED;      }
        else if(_whoisInfo.registrationType == REG_TYPE.REQUEST)
        {
            _subdomainRegRequests[nameHash] = domainName;

            // TODO: add events
            //emit registrationRequested(now, name);
            result = REG_RESULT.PENDING;     
        }
        else if(_whoisInfo.registrationType == REG_TYPE.MONEY)
        {
            // TODO: revisit
            // TODO: possibly need tvmRawReserve()
            result = (msg.value > _whoisInfo.subdomainRegPrice ? REG_RESULT.APPROVED : REG_RESULT.NOT_ENOUGH_MONEY);
        }
        else if(_whoisInfo.registrationType == REG_TYPE.OWNER)
        {
            bool ownerCalled = (ownerAddress == _whoisInfo.ownerAddress && ownerPubkey == _whoisInfo.ownerPubkey);
            result = ownerCalled ? REG_RESULT.APPROVED : REG_RESULT.DENIED;            
        }

        // Return the change
        return{value: 0, flag: 64}(result);
    }
    
    function _callbackOnRegistrationRequest(REG_RESULT result) internal
    {
        _whoisInfo.lastRegResult = result;
        
        if(result == REG_RESULT.APPROVED)
        {
            _whoisInfo.dtExpires = (now + ninetyDays);
        }
        else if(result == REG_RESULT.PENDING)
        {
            //
        }
        else if(result == REG_RESULT.DENIED)
        {
            _whoisInfo.ownerAddress = addressZero;
            _whoisInfo.ownerPubkey  = 0;
            _whoisInfo.dtExpires    = 0;
        }
        else if(result == REG_RESULT.NOT_ENOUGH_MONEY)
        { }
    }

    function callbackOnRegistrationRequest(REG_RESULT result) external override 
    {
        require(msg.sender == _whoisInfo.parentDomainAddress, 6578);
        tvm.accept();
        _callbackOnRegistrationRequest(result);
    }

    //========================================
    //
    function approveRegistration(string domainName) external override onlyOwner notExpired
    {
        // Check if the request exists, fast and easy
        uint256 nameHash = tvm.hash(domainName);
        require(_subdomainRegRequests.exists(nameHash), 6661);

        tvm.accept();

        (address addr, ) = calculateDomainAddress(domainName);
        IDnsRecord(addr).callbackOnRegistrationRequest(REG_RESULT.APPROVED);
        delete _subdomainRegRequests[nameHash];
    }

    function approveRegistrationAll() external override onlyOwner notExpired
    {
        tvm.accept();

        for( (, string domainName) : _subdomainRegRequests)
        {
            (address addr, ) = calculateDomainAddress(domainName);
            IDnsRecord(addr).callbackOnRegistrationRequest(REG_RESULT.APPROVED);
        }
        delete _subdomainRegRequests;
    }
    
    function denyRegistration(string domainName) external override onlyOwner notExpired
    {
        // Check if the request exists, fast and easy
        uint256 nameHash = tvm.hash(domainName);
        require(_subdomainRegRequests.exists(nameHash), 6661);

        tvm.accept();

        (address addr, ) = calculateDomainAddress(domainName);
        IDnsRecord(addr).callbackOnRegistrationRequest(REG_RESULT.DENIED);
        delete _subdomainRegRequests[nameHash];
    }
    
    function denyRegistrationAll() external override onlyOwner notExpired
    {
        tvm.accept();

        for( (, string domainName) : _subdomainRegRequests)
        {
            (address addr, ) = calculateDomainAddress(domainName);
            IDnsRecord(addr).callbackOnRegistrationRequest(REG_RESULT.DENIED);
        }
        delete _subdomainRegRequests;
    }
    
    //========================================
    //
    function withdrawBalance(uint128 amount, address dest) external override onlyOwner notExpired
    {        
        tvm.accept();

        dest.transfer(amount, false);
    }
}

//================================================================================
//
