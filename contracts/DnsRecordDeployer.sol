pragma ton-solidity >=0.42.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
import "./DnsRecordTEST.sol";

//================================================================================
//
contract DnsRecordDeployer
{
    //========================================
    // 
    TvmCell static _domainCode;
    
    //========================================
    //
    constructor() public 
    {
        tvm.accept();
    }

    //========================================
    //
    function deploy(string domainName, address ownerAddress) external returns (address)
    {
        uint128 minimumBalance = gasToValue(100000, 0) * 13; // 500k for minimum balance, 500k for local constructor, 300k for claimExpired();
        require(msg.value >= minimumBalance, 211); // ERROR_NOT_ENOUGH_MONEY
        
        uint128 balance = gasToValue(100000, 0);
        tvm.rawReserve(balance, 0);

        TvmCell stateInit = tvm.buildStateInit({
            contr: DnsRecord,
            varInit: {
                _domainName: domainName,
                _domainCode: _domainCode
            },
            code: _domainCode
        });

        address domainAddress = new DnsRecord{value: 0, flag: 128, stateInit: stateInit}(ownerAddress, true);
        return domainAddress;
    }
}

//================================================================================
//
