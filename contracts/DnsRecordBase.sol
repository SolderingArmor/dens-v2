pragma ton-solidity >= 0.42.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
import "../interfaces/IDnsRecord.sol";

//================================================================================
//
abstract contract DnsRecordBase is IDnsRecord, DnsFunctionsCommon
{
    //========================================
    // Variables
    string   internal static _domainName;
    bool     internal        _nameIsValid;
    TvmCell  internal static _domainCode;
    DnsWhois internal        _whoisInfo;

    //========================================
    // Getters
    function getDomainCode() external view override returns (TvmCell) {    return _domainCode;  }
    //
    function canProlongate() public   view override returns (bool   ) {    return (now <= _whoisInfo.dtExpires && 
                                                                                   now >= _whoisInfo.dtExpires - tenDays);  }
    function isExpired()     public   view override returns (bool   ) {    return  now >  _whoisInfo.dtExpires;             }
    // 
    function callWhois() external view responsible override returns (DnsWhois) {    _reserve();  return{value: 0, flag: 128}(_whoisInfo);  }
    function  getWhois() external view             override returns (DnsWhois) {                 return                      _whoisInfo;   }
    //
    function callEndpointAddress() external view responsible override returns (address) {    _reserve();  return{value: 0, flag: 128}(_whoisInfo.endpointAddress);  }
    function  getEndpointAddress() external view             override returns (address) {                 return                      _whoisInfo.endpointAddress;   }
 
    //========================================
    //
    function _reserve() internal view
    {
        uint128 balance = gasToValue(500000, 0);

        // When we deploy via new from another contract, "address(this).balance" shows 0 even if we have "msg.value"; 
        // this is a workaround;
        require(address(this).balance > balance || msg.value > balance, ERROR_NOT_ENOUGH_MONEY);
        
        // Reserve exactly minimum balance;
        tvm.rawReserve(balance, 0);
    }

    //========================================
    //
    function changeEndpointAddress(address newAddress) external override onlyOwner notExpired
    {
        _reserve();
        _whoisInfo.endpointAddress = newAddress;
        msg.sender.transfer(0, false, 128);
    }

    //========================================
    //
    function changeRegistrationType(REG_TYPE newType) external override onlyOwner notExpired
    {
        require(newType < REG_TYPE.NUM, ERROR_WRONG_REGISTRATION_TYPE);

        _reserve();
        _whoisInfo.registrationType = newType;
        msg.sender.transfer(0, false, 128);
    }

    //========================================
    //
    function changeRegistrationPrice(uint128 newPrice) external override onlyOwner notExpired
    {
        _reserve();
        _whoisInfo.registrationPrice = newPrice;
        msg.sender.transfer(0, false, 128);
    }

    //========================================
    //
    function changeComment(string newComment) external override onlyOwner notExpired
    {
        _reserve();
        _whoisInfo.comment = newComment;
        msg.sender.transfer(0, false, 128);
    }

    //========================================
    //
    function _changeOwner(address newOwnerAddress) internal
    {
        _whoisInfo.ownerAddress      = newOwnerAddress; //
        _whoisInfo.endpointAddress   = addressZero;     //
        _whoisInfo.registrationType  = REG_TYPE.DENY;   // prevent unwanted subdomains from registering by accident right after domain modification;
        _whoisInfo.registrationPrice = 0;               //
        _whoisInfo.comment           = "";              //
    }

    function changeOwner(address newOwnerAddress) external override onlyOwner notExpired
    {
        require(newOwnerAddress != addressZero,             ERROR_ADDRESS_CAN_NOT_BE_EMPTY    );
        require(newOwnerAddress != _whoisInfo.ownerAddress, ERROR_CAN_NOT_TRANSFER_TO_YOURSELF);
        
        _reserve();

        emit ownerChanged(now, _whoisInfo.ownerAddress, newOwnerAddress);

        _changeOwner(newOwnerAddress);
        _whoisInfo.totalOwnersNum += 1;
        msg.sender.transfer(0, false, 128);
    }

    //========================================
    //
    function prolongate() external override onlyOwner notExpired
    {
        require(canProlongate(), ERROR_CAN_NOT_PROLONGATE_YET);
        
        _reserve();
        _whoisInfo.dtExpires += ninetyDays;

        emit domainProlongated(now, _whoisInfo.dtExpires);

        msg.sender.transfer(0, false, 128);
    }

    //========================================
    //
    /// @dev dangerous function;
    //
    function releaseDomain() external override onlyOwner notExpired
    {
        _reserve();

        _changeOwner(addressZero);  
        _whoisInfo.dtExpires = 0;

        emit domainReleased(now);
        
        msg.sender.transfer(0, false, 128);
    }

    //========================================
    // Modifiers
    modifier onlyOwner
    {
        // Owner can make changes only after registration process is completed;
        require(_whoisInfo.ownerAddress == msg.sender && msg.sender != addressZero, ERROR_MESSAGE_SENDER_IS_NOT_MY_OWNER);
        _;
    }

    modifier onlyRoot
    {
        require(_whoisInfo.parentDomainAddress == msg.sender && msg.sender != addressZero, ERROR_MESSAGE_SENDER_IS_NOT_MY_ROOT);
        _;
    }

    modifier notExpired
    {
        require(!isExpired(), ERROR_DOMAIN_IS_EXPIRED);
        _;
    }

    modifier Expired
    {
        require(isExpired(), ERROR_DOMAIN_IS_NOT_EXPIRED);
        _;
    }

    modifier NameIsValid
    {
        require(_nameIsValid, ERROR_DOMAIN_NAME_NOT_VALID);
        _;
    }
}

//================================================================================
//