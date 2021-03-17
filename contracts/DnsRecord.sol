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
    function calculateFutureAddress(bytes domainName) public view override returns (address, TvmCell)
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
        _whoisInfo.segmentsCount          = uint8(segments.length);
        _whoisInfo.parentDomainName       = parentName;
       (_whoisInfo.parentDomainAddress, ) = calculateFutureAddress(parentName);
    }

    //========================================
    //
    
}

//================================================================================
//
