pragma ton-solidity >=0.38.2;
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
        // _validateDomainName() is very expensive, can't do anything without tvm.accept() first;
        // Be sure that you use a valid "_domainName", otherwise you will loose your Crystyals;
        
        tvm.accept();
        require(_validateDomainName(_domainName), ERROR_DOMAIN_NAME_NOT_VALID);

        (bytes[] segments, bytes parentName) = _parseDomainName(_domainName);
        _whoisInfo.segmentsCount             = uint8(segments.length);
        _whoisInfo.domainName                = _domainName;
        _whoisInfo.parentDomainName          = parentName;
       (_whoisInfo.parentDomainAddress, )    = calculateDomainAddress(parentName);
        
        // Registering a new domain is the same as claiming the expired from this point:
        claimExpired(ownerAddress, ownerPubkey);
    }

    //========================================
    //
    /// @dev TODO: here "external" was purposely changed to "public", otherwise you get the following error:
    ///      Error: Undeclared identifier. "claimExpired" is not (or not yet) visible at this point.
    ///      The fix is coming: https://github.com/tonlabs/TON-Solidity-Compiler/issues/36
    function claimExpired(address newOwnerAddress, uint256 newOwnerPubkey) public override 
    {
        require(isExpired(), ERROR_DOMAIN_IS_NOT_EXPIRED);
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
    
    //========================================
    //
    function sendRegistrationRequest(uint128 tonsToInclude) external override onlyOwner notExpired
    {
        // TODO:
        tvm.accept();
        uint128 tonsWithGas = 0 + tonsToInclude;// + gasToValue(10000, 0);
        IDnsRecord(_whoisInfo.parentDomainAddress).receiveRegistrationRequest{value: tonsWithGas, callback: IDnsRecord.callbackOnRegistrationRequest}(_domainName, _whoisInfo.ownerAddress, _whoisInfo.ownerPubkey);
    }
    
    //========================================
    //
    function receiveRegistrationRequest(string domainName, address ownerAddress, uint256 ownerPubkey) external responsible override returns (REG_RESULT)
    {
        // TODO:
        // 1. Check if the request exists;
        uint256 nameHash = tvm.hash(domainName);
        require(!_subdomainRegRequests.exists(nameHash), ERROR_DOMAIN_REG_REQUEST_ALREADY_EXISTS);

        // 2. Check if it is really my subdomain;
        (, string parentName) = _parseDomainName(domainName);
        require(parentName == _whoisInfo.domainName, ERROR_MESSAGE_SENDER_IS_NOT_MY_SUBDOMAIN);

        // 3. Check if the request came from domain itself;
        (address addr, ) = calculateDomainAddress(domainName);
        require(addr == msg.sender, ERROR_MESSAGE_SENDER_IS_NOT_VALID);

        // Calculate the result based on registration type;
        REG_RESULT result;
             if(_whoisInfo.registrationType == REG_TYPE.FFA)    {    result = REG_RESULT.APPROVED;    }
        else if(_whoisInfo.registrationType == REG_TYPE.DENY)   {    result = REG_RESULT.DENIED;      }
        else if(_whoisInfo.registrationType == REG_TYPE.REQUEST)
        {
            _subdomainRegRequests[nameHash] = domainName;
            emit newSubdomainRegistrationRequest(now, domainName);
            
            result = REG_RESULT.PENDING;     
        }
        else if(_whoisInfo.registrationType == REG_TYPE.MONEY)
        {
            result = (msg.value > _whoisInfo.subdomainRegPrice ? REG_RESULT.APPROVED : REG_RESULT.NOT_ENOUGH_MONEY);

            if(result == REG_RESULT.APPROVED)
            {
                uint128 toReserve = address(this).balance - msg.value + _whoisInfo.subdomainRegPrice;
                tvm.rawReserve(toReserve, 0); // flag 0 means "exactly X nanograms"
            }
        }
        else if(_whoisInfo.registrationType == REG_TYPE.OWNER)
        {
            bool ownerCalled = (ownerAddress == _whoisInfo.ownerAddress && ownerPubkey == _whoisInfo.ownerPubkey);
            result = ownerCalled ? REG_RESULT.APPROVED : REG_RESULT.DENIED;            
        }

        // Statistics
        if(result == REG_RESULT.APPROVED)
        {
            // 1.
            _whoisInfo.subdomainRegAccepted += 1;
            emit newSubdomainRegistered(now, domainName);
            
            // 2.
            if(_whoisInfo.registrationType == REG_TYPE.MONEY)
            {
                _whoisInfo.totalFeesCollected += _whoisInfo.subdomainRegPrice;
            }
        }
        else if(result == REG_RESULT.DENIED)
        {
            _whoisInfo.subdomainRegDenied += 1;
        }

        // Return the change
        return{value: 0, flag: 64}(result);
    }
    
    //========================================
    //
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

    //========================================
    //
    function callbackOnRegistrationRequest(REG_RESULT result) external override onlyRoot
    {
        tvm.accept();
        _callbackOnRegistrationRequest(result);
    }

    //========================================
    //
    function approveRegistration(string domainName) external override onlyOwner notExpired
    {
        // Check if the request exists, fast and easy
        uint256 nameHash = tvm.hash(domainName);
        require(_subdomainRegRequests.exists(nameHash), ERROR_DOMAIN_REG_REQUEST_DOES_NOT_EXIST);

        tvm.accept();

        (address addr, ) = calculateDomainAddress(domainName);
        IDnsRecord(addr).callbackOnRegistrationRequest(REG_RESULT.APPROVED);

        emit newSubdomainRegistered(now, domainName);
        _whoisInfo.subdomainRegAccepted += 1;

        delete _subdomainRegRequests[nameHash];
    }

    //========================================
    //
    function approveRegistrationAll() external override onlyOwner notExpired
    {
        tvm.accept();

        uint32 counter = 0;

        for( (, string domainName) : _subdomainRegRequests)
        {
            (address addr, ) = calculateDomainAddress(domainName);
            IDnsRecord(addr).callbackOnRegistrationRequest(REG_RESULT.APPROVED);

            emit newSubdomainRegistered(now, domainName);
            counter += 1;
        }

        _whoisInfo.subdomainRegAccepted += counter;
        delete _subdomainRegRequests;
    }
    
    //========================================
    //
    function denyRegistration(string domainName) external override onlyOwner notExpired
    {
        // Check if the request exists, fast and easy
        uint256 nameHash = tvm.hash(domainName);
        require(_subdomainRegRequests.exists(nameHash), ERROR_DOMAIN_REG_REQUEST_DOES_NOT_EXIST);

        tvm.accept();

        (address addr, ) = calculateDomainAddress(domainName);
        IDnsRecord(addr).callbackOnRegistrationRequest(REG_RESULT.DENIED);
        
        _whoisInfo.subdomainRegDenied += 1;
        delete _subdomainRegRequests[nameHash];
    }
    
    //========================================
    //
    function denyRegistrationAll() external override onlyOwner notExpired
    {
        tvm.accept();

        uint32 counter = 0;

        for( (, string domainName) : _subdomainRegRequests)
        {
            (address addr, ) = calculateDomainAddress(domainName);
            IDnsRecord(addr).callbackOnRegistrationRequest(REG_RESULT.DENIED);
        }

        _whoisInfo.subdomainRegDenied += counter;
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
