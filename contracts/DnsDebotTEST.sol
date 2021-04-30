pragma ton-solidity >=0.42.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
/// @title DNSDebot
/// @author Augual.Team
/// @notice Debot for Augual.DeNS service

//================================================================================
//
import "../contracts/DnsRecordTEST.sol";
import "../interfaces/IDnsRecord.sol";
import "../interfaces/IDebot.sol";
import "../interfaces/debot/sdk.sol";
import "../interfaces/debot/terminal.sol";
import "../interfaces/debot/address.sol";
import "../interfaces/debot/number.sol";

//================================================================================
//
interface IMsig 
{
    /// @dev Allows custodian if she is the only owner of multisig to transfer funds with minimal fees.
    /// @param dest Transfer target address.
    /// @param value Amount of funds to transfer.
    /// @param bounce Bounce flag. Set true if need to transfer funds to existing account;
    /// set false to create new account.
    /// @param flags `sendmsg` flags.
    /// @param payload Tree of cells used as body of outbound internal message.
    function sendTransaction(
        address dest,
        uint128 value,
        bool bounce,
        uint8 flags,
        TvmCell payload) external view;
}

//================================================================================
//
abstract contract Upgradable 
{
    /// @notice Allows to upgrade contract code and data.
    /// @param state Root cell with StateInit structure of the new contract.
    /// Remark: only code is used from this structure.
    function upgrade(TvmCell state) public virtual 
    {
        require(msg.pubkey() == tvm.pubkey(), 100);
        TvmCell newcode = state.toSlice().loadRef();
        tvm.accept();
        tvm.commit();
        tvm.setcode(newcode);
        tvm.setCurrentCode(newcode);
        onCodeUpgrade();
    }

    function onCodeUpgrade() internal virtual;
}

//================================================================================
//
contract DnsDebot is Debot, Upgradable, DnsFunctionsCommon
{
    TvmCell static _domainCode;
    
    address  msigAddress;
    string   ctx_name;
    address  ctx_domain;
    DnsWhois ctx_whois;
    int8     ctx_accState;
    uint8    ctx_segments;
    address  ctx_parent;
    uint256  amountToAttach;

    optional(uint256) emptyPk;
    
	//========================================
    //
	function getRequiredInterfaces() public pure returns (uint256[] interfaces) 
    {
        return [Terminal.ID, AddressInput.ID, NumberInput.ID];
	}

    //========================================
    //
    function getDebotInfo() public functionID(0xDEB) view returns(string name,     string version, string publisher, string key,  string author,
                                                                  address support, string hello,   string language,  string dabi, bytes icon)
    {
        name      = "DnsDeBot";
        version   = "0.1.0";
        publisher = "Augual.TEAM";
        key       = "DeBot for Augual.DeNS";
        author    = "Augual.TEAM";
        support   = addressZero;
        hello     = "Welcome to DeNS DeBot (TEST)!";
        language  = "en";
        dabi      = m_debotAbi.hasValue() ? m_debotAbi.get() : "";
        icon      = "";
    }

    //========================================
    /// @notice Define DeBot version and title here.
    function getVersion() public override returns (string name, uint24 semver) 
    {
        (name, semver) = ("DnsDebot", _version(0, 1, 0));
    }

    function _version(uint24 major, uint24 minor, uint24 fix) private pure inline returns (uint24) 
    {
        return (major << 16) | (minor << 8) | (fix);
    }    

    //========================================
    // Implementation of Upgradable
    function onCodeUpgrade() internal override 
    {
        tvm.resetStorage();
    }    

    //========================================
    /// @notice Entry point function for DeBot.    
    function start() public override 
    {
        mainMenu();
    }

    //========================================
    //
    function mainMenu() public 
    {
        _eraseCtx();
        Terminal.input(tvm.functionId(onPathEnter), "Enter DeNS string:", false);
    }

    //========================================
    //
    function onMsigEnter(address value) public
    {  
        msigAddress = value;
        
        Terminal.print(0, "Please enter amount of TONs you wish to attach to the Claim message (can be 0)."); 
        Terminal.print(0, "NOTE: additional 1.5 TON will be added to cover all the fees, the change will be returned back to Multisig.");

        if(ctx_accState == -1 || ctx_accState == 0)
        {
            NumberInput.get(tvm.functionId(onMsigEnter_2), "Enter amount: ", 0, 999999999999999);
        }
        else if(now > ctx_whois.dtExpires)
        {
            NumberInput.get(tvm.functionId(onClaimExpired), "Enter amount: ", 0, 999999999999999);
        }
        else 
        {
            // We actually caan't get here
            mainMenu();
        }
    }

    function onMsigEnter_2(int256 value) public 
    {        
        TvmCell body = tvm.encodeBody(DnsDebot.deploy, ctx_name, msigAddress);

        IMsig(msigAddress).sendTransaction{
            abiVer: 2,
            extMsg: true,
            sign: true,
            callbackId: 0,
            onErrorId: tvm.functionId(onError),
            time: uint32(now),
            expire: 0,
            pubkey: 0x00
        }(address(this),
          1.5 ton + uint128(value),
          false,
          1,
          body);

        Terminal.print(0, "Claim requested!");
        Terminal.print(0, "Please give it ~10 seconds to process and then reload whois to get latest domain information.\n");
        onPathEnter(ctx_name);
    }        

    //========================================
    //
    function deploy(string domainName, address ownerAddress) external returns (address)
    {
        require(msg.value >= 1.3 ton, ERROR_NOT_ENOUGH_MONEY);
        tvm.rawReserve(0.1 ton, 0);

        (, TvmCell image) = _calculateDomainAddress(domainName); 

        new DnsRecord{value: 0, flag: 128, stateInit: image}(ownerAddress, true);
    }

    //========================================
    //
    function onDeploySuccess(address value) public 
    {
        address domainAddr = value;
        Terminal.print(0, format("Domain address: 0:{:x}", domainAddr.value)); 
        mainMenu(); 
    }    

    //========================================
    //
    function onError(uint32 sdkError, uint32 exitCode) public 
    {
        Terminal.print(0, format("Failed! SDK Error: {}. Exit Code: {}", sdkError, exitCode));
        mainMenu(); 
    }    
 
    //========================================
    //
    function onPathEnter(string value) public 
    { 
        bool isValid = _validateDomainName(value);
        if(!isValid)
        {
            Terminal.print(0, format("Domain \"{}\" is is not valid!", value));
            Terminal.print(0, " > Domain can have up to 4 segments;");
            Terminal.print(0, " > Each segment can have only numbers, dash \"-\" and lowercase letters;");
            Terminal.print(0, " > Segment separator is shash \"/\";\n");

            mainMenu();
            return;
        }

        (ctx_domain, ) = _calculateDomainAddress(value);
        ctx_name = value;

        // Get parent information
        (string[] segments, string parentName) = _parseDomainName(value);
        ctx_segments   = uint8(segments.length);
        (ctx_parent, ) = _calculateDomainAddress(parentName);

        Terminal.print(0, format("Domain address: 0:{:x}", ctx_domain.value)); 

        // TODO: add parent registration type (and price if needed) to show here
        Sdk.getAccountType(tvm.functionId(onAddressCheck), ctx_domain);
    } 

    //========================================
    //
    function onAddressCheck(int8 acc_type) public 
    {
        ctx_accState = acc_type;
        if (ctx_accState == -1 || ctx_accState == 0) 
        {
            Terminal.print(0, format("Domain ({}) is FREE", ctx_name));
            Terminal.print(0, "1)    [Deploy and claim domain]"); 
            Terminal.print(0, "2)    [Enter another DeNS name]");                                   
            NumberInput.get(tvm.functionId(onFree), "Enter your choice: ", 1,2);            
        }
        else if (ctx_accState == 1)
        {
            Terminal.print(0, format("Domain ({}) is ACTIVE", ctx_name));         
            IDnsRecord(ctx_domain).getWhois{
                        abiVer: 2,
                        extMsg: true,
                        sign: false,
                        time: uint64(now),
                        expire: 0,
                        pubkey: emptyPk,
                        callbackId: tvm.functionId(onWhoIs),
                        onErrorId: tvm.functionId(onError)
                        }();   
        } 
        else if (ctx_accState == 2)
        {
            Terminal.print(0, format("Domain ({}) is FROZEN", ctx_name));
            mainMenu(); 
        }
    } 

    //========================================
    //
    function onFree(int256 value) public
    {
        if(value == 1)
        {
            AddressInput.get(tvm.functionId(onMsigEnter), "Enter owner wallet: ");  
        }
        else
        {        
            mainMenu();
        }
    }   

    //========================================
    //
    function onWhoIs(DnsWhois _whoisInfo) public 
    {
        ctx_whois = _whoisInfo;

        Terminal.print(0, "");
        Terminal.print(0, format("Domain Name: {}",          ctx_whois.domainName));            // domain name
        Terminal.print(0, format("Domain Comment: {}",       ctx_whois.comment));               // comment
        Terminal.print(0, format("Endpoint Address: 0:{:x}", ctx_whois.endpointAddress.value)); // endpoint address
        Terminal.print(0, format("Owner Address: 0:{:x}",    ctx_whois.ownerAddress.value));    // owner address
        Terminal.print(0, format("Creation Date: {}",        ctx_whois.dtCreated));             // creation date
        Terminal.print(0, format("Expiration Date: {}",      ctx_whois.dtExpires));             // expiration date
        Terminal.print(0, format("Last Prolong Date: {}",    ctx_whois.dtLastProlongation));    // last prolongation date

             if (ctx_whois.registrationType == REG_TYPE.FFA)   {    Terminal.print(0, "Registration Type: FFA");    } // subdomain registration type
        else if (ctx_whois.registrationType == REG_TYPE.DENY)  {    Terminal.print(0, "Registration Type: DENY");   } // subdomain registration type
        else if (ctx_whois.registrationType == REG_TYPE.OWNER) {    Terminal.print(0, "Registration Type: OWNER");  } // subdomain registration type
        else if (ctx_whois.registrationType == REG_TYPE.MONEY) {    Terminal.print(0, "Registration Type: MONEY");  } // subdomain registration type
        else                                                   {    Terminal.print(0, "Registration Type: OTHER");  } // subdomain registration type
        
        Terminal.print(0, format("Registration Price: {}", ctx_whois.registrationPrice)); // subdomain registration price
        Terminal.print(0, "");

        if(now > ctx_whois.dtExpires)
        {
            Terminal.print(0, format("Domain ({}) EXPIRED! You can try and claim it.", ctx_name));
            Terminal.print(0, "1)    [Claim]");
            Terminal.print(0, "2)    [Reload Whois]");
            Terminal.print(0, "3)    [Enter another DeNS name]");
            NumberInput.get(tvm.functionId(onExpired), "Enter your choice: ", 1, 3);  
        }
        else 
        {
            Terminal.print(0, "1)    [Manage domain]");
            Terminal.print(0, "2)    [Reload Whois]");
            Terminal.print(0, "3)    [Enter another DeNS name]");
            NumberInput.get(tvm.functionId(onActive), "Enter your choice: ", 1, 3);  
        }
    }

    //========================================
    //
    function onActive(int256 value) public
    {
        if(value == 2)
        {
            onAddressCheck(ctx_accState);
            return;
        }
        if(value == 3)
        {
            mainMenu();
            return;
        }
  
        Terminal.print(0, "1)    [Change Endpoint]"); 
        Terminal.print(0, "2)    [Change Owner]");      
        Terminal.print(0, "3)    [Change Registration Type]");      
        Terminal.print(0, "4)    [Change Registration Price]");    
        Terminal.print(0, "5)    [Change Comment]");    
        if (canProlongate()) {
            Terminal.print(0, "6)    [Prolong]");    
        } 
        Terminal.print(0, "7)    [Back]");     
        Terminal.print(0, "8)    [Enter another DeNS name]");    

        NumberInput.get(tvm.functionId(manageMenu), "Enter your choice: ", 1, 8);    
    }

    //========================================
    //
    function onExpired(int256 value) public
    {
        if(value == 2)
        {
            onAddressCheck(ctx_accState);
            return;
        }
        if(value == 3)
        {
            mainMenu();
            return;
        }

        //Terminal.print(0, "Please enter amount of TONs you wish to attach to the claim message (can be 0)."); 
        //Terminal.print(0, "NOTE: additional 1.5 TON will be added to cover all the fees, the change will be returned to Multisig.");      
        //NumberInput.get(tvm.functionId(onClaimExpired), "Enter amount: ", 0, 999999999999999);
        AddressInput.get(tvm.functionId(onMsigEnter), "Enter owner wallet: ");  
    }

    //========================================
    //
    function manageMenu(int256 value) public 
    {
             if (value == 1) {    AddressInput.get(tvm.functionId(onChangeEndpoint), "Enter new endpoint: "                      );  }
        else if (value == 2) {    AddressInput.get(tvm.functionId(onChangeOwner),    "Enter new owner: "                         );  } 
        else if (value == 3) {    NumberInput.get(tvm.functionId(onChangeRegType),   "Enter new type (0-3): ", 0, 3              );  }
        else if (value == 4) {    NumberInput.get(tvm.functionId(onChangePrice),     "Enter new price: ",      1, 999999999999999);  } 
        else if (value == 5) {    Terminal.input (tvm.functionId(onChangeComment),   "Enter new comment: ",    false             );  } 
        else if (value == 6) 
        {
            TvmCell body = tvm.encodeBody(IDnsRecord.prolongate);
            _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);
        } 
        else if (value == 7)
        {
            // reload whois and show it one more time
            onAddressCheck(ctx_accState);
        }
        else
        {
            mainMenu();
        }                                
    }    

    //========================================
    //
    function onChangeEndpoint(address value) public 
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.changeEndpointAddress, value);
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(ctx_accState);
    }      

    //========================================
    //
    function onChangeOwner(address value) public 
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.changeOwner, value);
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(ctx_accState);
    }         

    //========================================
    //
    function onChangeRegType(int256 value) public
    {
        if(value >= int256(REG_TYPE.NUM))
        {
            Terminal.print(0, "Error! Registration Type should be between 0 and 3!");
            
            // Show domain management nemu again
            onActive(1);
            return;
        }

        TvmCell body = tvm.encodeBody(IDnsRecord.changeRegistrationType, REG_TYPE(value));
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(ctx_accState);
    }     

    //========================================
    //
    function onChangePrice(int256 value) public
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.changeRegistrationPrice, uint128(value));
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(ctx_accState);
    }     

    //========================================
    //
    function onChangeComment(string value) public
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.changeComment, value);
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(ctx_accState);
    }            

    //========================================
    //
    function onClaimExpired(int256 value) public
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.claimExpired, msigAddress, true);
        _sendTransact(msigAddress, ctx_domain, body, uint128(value) + 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(ctx_accState);
    }            

    //========================================
    //
    function _calculateDomainAddress(string domainName) public view returns (address, TvmCell)
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
    function _eraseCtx() internal 
    {
        msigAddress    = addressZero;
        ctx_domain     = addressZero;  
        ctx_name       = "";
        ctx_accState   = 0;
        ctx_segments   = 0;
        ctx_parent     = addressZero;
        amountToAttach = 0;
    }    

    //========================================
    //
    function _sendTransact(address msigAddr, address dest, TvmCell payload, uint128 grams) internal pure
    {
        IMsig(msigAddr).sendTransaction{
            abiVer: 2,
            extMsg: true,
            sign: true,
            callbackId: 0,
            onErrorId: tvm.functionId(onError),
            time: uint32(now),
            expire: 0,
            pubkey: 0x00
        }(dest,
          grams,
          false,
          1,
          payload);
    }        

    function canProlongate() public   view returns (bool) {    return (now <= ctx_whois.dtExpires && 
                                                                       now >= ctx_whois.dtExpires - tenDays);  }
    function isExpired()     public   view returns (bool) {    return  now >  ctx_whois.dtExpires;             }
    // 
}

//================================================================================
//