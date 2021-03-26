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

        (string[] segments, string parentName) = _parseDomainName(_domainName);
        _whoisInfo.segmentsCount               = uint8(segments.length);
        _whoisInfo.domainName                  = _domainName;
        _whoisInfo.parentDomainName            = parentName;
       (_whoisInfo.parentDomainAddress, )      = calculateDomainAddress(parentName);
        _whoisInfo.dtCreated                   = now;
        _whoisInfo.dtExpires                   = 0; // sanity
        
        // Registering a new domain is the same as claiming the expired from this point:
        _claimExpired(ownerAddress, ownerPubkey, 0);
    }

    //========================================
    //
    function _claimExpired(address newOwnerAddress, uint256 newOwnerPubkey, uint128 tonsToInclude) internal 
    {
        // reset ownership first
        changeOwnership(addressZero, 0);

        // if it is a ROOT domain name
        if(_whoisInfo.segmentsCount == 1) 
        {
            // Root domains won't need approval, internal callback right away
            _callbackOnRegistrationRequest(REG_RESULT.APPROVED, newOwnerAddress, newOwnerPubkey);
        }
        else if(tonsToInclude > 0)
        {
            _sendRegistrationRequest(tonsToInclude);
        }
    }
    
    /// @dev TODO: here "external" was purposely changed to "public", otherwise you get the following error:
    ///      Error: Undeclared identifier. "claimExpired" is not (or not yet) visible at this point.
    ///      The fix is coming: https://github.com/tonlabs/TON-Solidity-Compiler/issues/36
    function claimExpired(address newOwnerAddress, uint256 newOwnerPubkey, uint128 tonsToInclude) public override Expired 
    {
        require(msg.pubkey() == 0 && msg.sender != addressZero, ERROR_REQUIRE_INTERNAL_MESSAGE_WITH_VALUE);

        _claimExpired(newOwnerAddress, newOwnerPubkey, tonsToInclude);
    }
    
    function releaseDomain() external override onlyOwner notExpired
    {
        tvm.accept();

        _whoisInfo.ownerAddress     = addressZero;
        _whoisInfo.ownerPubkey      = 0;
        _whoisInfo.endpointAddress  = addressZero;
        _whoisInfo.registrationType = REG_TYPE.DENY;
        _whoisInfo.comment          = "";
        _whoisInfo.dtExpires        = 0;

        emit domainReleased(now);
    }

    //========================================
    //
    function _sendRegistrationRequest(uint128 tonsToInclude) internal
    {
        // flag + 1 - means that the sender wants to pay transfer fees separately from contract's balance,
        // because we want to send exactly "tonsToInclude" amount;
        IDnsRecord(_whoisInfo.parentDomainAddress).receiveRegistrationRequest{value: tonsToInclude, callback: IDnsRecord.callbackOnRegistrationRequest, flag: 1}(_domainName, _whoisInfo.ownerAddress, _whoisInfo.ownerPubkey);
    }
    
    //========================================
    //
    function receiveRegistrationRequest(string domainName, address ownerAddress, uint256 ownerPubkey) external responsible override returns (REG_RESULT, address, uint256)
    {
        //========================================
        // 1. Check if the request exists;
        //uint256 nameHash = tvm.hash(domainName);
        //require(!_subdomainRegRequests.exists(nameHash), ERROR_DOMAIN_REG_REQUEST_ALREADY_EXISTS);

        // 2. Check if it is really my subdomain;
        (, string parentName) = _parseDomainName(domainName);
        require(parentName == _whoisInfo.domainName, ERROR_MESSAGE_SENDER_IS_NOT_MY_SUBDOMAIN);

        // 3. Check if the request came from domain itself;
        (address addr, ) = calculateDomainAddress(domainName);
        require(addr == msg.sender, ERROR_MESSAGE_SENDER_IS_NOT_VALID);

        //========================================
        // REG_TYPE.MONEY has a custom flow;
        if(_whoisInfo.registrationType == REG_TYPE.MONEY && msg.value >= _whoisInfo.subdomainRegPrice)
        {
            tvm.accept();
            _whoisInfo.subdomainRegAccepted += 1;
            _whoisInfo.totalFeesCollected   += _whoisInfo.subdomainRegPrice;
            emit newSubdomainRegistered(now, domainName, _whoisInfo.subdomainRegPrice);
            
            return{value: 0, flag: 0}(REG_RESULT.APPROVED, ownerAddress, ownerPubkey); // we don't return ANY change in this case
        }

        //========================================
        // General flow;
        REG_RESULT result;
             if(_whoisInfo.registrationType == REG_TYPE.FFA)    {    result = REG_RESULT.APPROVED;    }
        else if(_whoisInfo.registrationType == REG_TYPE.DENY)   {    result = REG_RESULT.DENIED;      }
        else if(_whoisInfo.registrationType == REG_TYPE.MONEY)
        {
            // If we are here that means "REG_TYPE.MONEY" custom flow was unsuccessful;
            result = REG_RESULT.NOT_ENOUGH_MONEY;
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
            emit newSubdomainRegistered(now, domainName, 0);
        }
        else if(result == REG_RESULT.DENIED)
        {
            _whoisInfo.subdomainRegDenied += 1;
        }

        // Return the change
        return{value: 0, flag: 64}(result, ownerAddress, ownerPubkey);
    }
    
    //========================================
    //
    function _callbackOnRegistrationRequest(REG_RESULT result, address ownerAddress, uint256 ownerPubkey) internal
    {
        emit registrationResult(now, result, ownerAddress, ownerPubkey);
        _whoisInfo.lastRegResult = result;
        
        if(result == REG_RESULT.APPROVED)
        {
            _whoisInfo.ownerAddress    = ownerAddress;
            _whoisInfo.ownerPubkey     = ownerPubkey;
            _whoisInfo.dtExpires       = (now + ninetyDays);
            _whoisInfo.totalOwnersNum += 1;
        }
        else if(result == REG_RESULT.DENIED || result == REG_RESULT.NOT_ENOUGH_MONEY)
        {
            // Domain ownership is reset
            _whoisInfo.ownerAddress = addressZero;
            _whoisInfo.ownerPubkey  = 0;
            _whoisInfo.dtExpires    = 0;
        }
    }

    //========================================
    //
    function callbackOnRegistrationRequest(REG_RESULT result, address ownerAddress, uint256 ownerPubkey) external override onlyRoot Expired
    {
        tvm.accept();
        _callbackOnRegistrationRequest(result, ownerAddress, ownerPubkey);
    }
}

//================================================================================
//
