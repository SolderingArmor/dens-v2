pragma ton-solidity >=0.42.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
import "../contracts/DnsRecordTEST.sol";

//================================================================================
//
contract DnsRecordDeployer
{
    //========================================
    // 
    string  static _domainName;
    TvmCell static _domainCode;
    address static _msigAddress;
    uint256 static _magicNumber;
    
    //========================================
    //
    function _calculateDomainAddress(string domainName) internal view returns (address, TvmCell)
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
    constructor(address ownerAddress) public
    {
        tvm.accept();
        (, TvmCell stateInit) = _calculateDomainAddress(_domainName);

        address domainAddress = new DnsRecord{value: 0, flag: 128, stateInit: stateInit}(ownerAddress, false);
    }

    receive() external 
    {
        (address domainAddress, ) = _calculateDomainAddress(_domainName);
        require(msg.sender == domainAddress, 777); // accept only messages or bounces from DnsRecord
        _msigAddress.transfer(0, false, 128+32);
    }

    // The only time when we can get onBounce is when deployment fails. Send all money back to _msigAddress and selfdestruct;
    onBounce(TvmSlice body) external 
    {
        _msigAddress.transfer(0, false, 128+32);
    }
}

//================================================================================
//