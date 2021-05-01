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
import "../contracts/DnsRecord.sol";
import "../interfaces/IDnsRecord.sol";
import "../interfaces/IDebot.sol";
import "../interfaces/debot/address.sol";
import "../interfaces/debot/amount.sol";
import "../interfaces/debot/menu.sol";
import "../interfaces/debot/number.sol";
import "../interfaces/debot/sdk.sol";
import "../interfaces/debot/terminal.sol";

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

    optional(uint256) emptyPk;
    
	//========================================
    //
	function getRequiredInterfaces() public pure returns (uint256[] interfaces) 
    {
        return [Terminal.ID, AddressInput.ID, NumberInput.ID, AmountInput.ID, Menu.ID];
	}

    //========================================
    //
    function getDebotInfo() public functionID(0xDEB) view returns(string name,     string version, string publisher, string key,  string author,
                                                                  address support, string hello,   string language,  string dabi, bytes icon)
    {
        name      = "DNS DeBot (Augual.TEAM)";
        version   = "0.1.0";
        publisher = "Augual.TEAM";
        key       = "DeNS DeBot from Augual.TEAM";
        author    = "Augual.TEAM";
        support   = addressZero;
        hello     = "Welcome to DeNS DeBot!";
        language  = "en";
        dabi      = m_debotAbi.hasValue() ? m_debotAbi.get() : "";
        icon      = m_icon.hasValue()     ? m_icon.get()     : "";
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
        mainMenu(0);
    }

    //========================================
    //
    function mainMenu(uint32 index) public 
    {
        _eraseCtx();
        index = 0; // shut a warning
        Terminal.input(tvm.functionId(onPathEnter), "Enter domain name:", false);
    }

    //========================================
    //
    function onMsigEnter(address value) public
    {  
        msigAddress = value;
        
        Terminal.print(0, "Please enter amount of TONs to attach to the Claim message;"); 
        Terminal.print(0, "NOTE: additional 1.5 TON will be added to cover all the fees, the change will be returned back to Multisig.");

        if(ctx_accState == -1 || ctx_accState == 0)
        {
            AmountInput.get(tvm.functionId(onMsigEnter_2), "Enter amount: ", 9, 0, 999999999999999);
        }
        else if(now > ctx_whois.dtExpires)
        {
            AmountInput.get(tvm.functionId(onClaimExpired), "Enter amount: ", 9, 0, 999999999999999);
        }
    }

    function onMsigEnter_2(int256 value) public 
    {
        uint128 totalValue = 1.5 ton + uint128(value);
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
          totalValue,
          false,
          1,
          body);

        Terminal.print(0, "Claim requested!");
        Terminal.print(0, "Please give it ~15 seconds to process and then reload whois to get latest domain information.\n");
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
        mainMenu(0); 
    }    

    //========================================
    //
    function onError(uint32 sdkError, uint32 exitCode) public 
    {
        Terminal.print(0, format("Failed! SDK Error: {}. Exit Code: {}", sdkError, exitCode));
        mainMenu(0); 
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

            mainMenu(0);
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
        Sdk.getAccountType(tvm.functionId(saveAccState), ctx_domain);
    } 

    //========================================
    //
    function saveAccState(int8 acc_type) public 
    {
        ctx_accState = acc_type;
        onAddressCheck(0);
    }

    //========================================
    //
    function onAddressCheck(uint32 index) public 
    {
        index = 0;
        //ctx_accState = acc_type;
        if (ctx_accState == -1 || ctx_accState == 0) 
        {
            Terminal.print(0, format("Domain ({}) is FREE and not deployed.", ctx_name));
            Terminal.print(0, "What would you like to do?");

            MenuItem[] mi;
            mi.push(MenuItem("Deploy and claim domain",   "", tvm.functionId(onFree)        ));
            mi.push(MenuItem("Refresh Whois",             "", tvm.functionId(onRefreshWhois)));
            mi.push(MenuItem("Enter another domain name", "", tvm.functionId(mainMenu)      ));
            Menu.select("Enter your choice: ", "", mi);
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
                        onErrorId:  tvm.functionId(onError)
                        }();   
        } 
        else if (ctx_accState == 2)
        {
            Terminal.print(0, format("Domain ({}) is FROZEN", ctx_name));
            mainMenu(0); 
        }
    } 

    //========================================
    //
    function onFree(uint32 index) public
    {
        index = 0; // shut a warning
        AddressInput.get(tvm.functionId(onMsigEnter), "Enter owner Multisig address: ");
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

             if (ctx_whois.registrationType == REG_TYPE.FFA)   {    Terminal.print(0, "Registration Type: FFA");    } //
        else if (ctx_whois.registrationType == REG_TYPE.DENY)  {    Terminal.print(0, "Registration Type: DENY");   } //
        else if (ctx_whois.registrationType == REG_TYPE.OWNER) {    Terminal.print(0, "Registration Type: OWNER");  } //
        else if (ctx_whois.registrationType == REG_TYPE.MONEY) {    Terminal.print(0, "Registration Type: MONEY");  } //
        else                                                   {    Terminal.print(0, "Registration Type: OTHER");  } //
        
        Terminal.print(0, format("Registration Price: {:t}", ctx_whois.registrationPrice)); // subdomain registration price
        Terminal.print(0, "");

        //if(now > ctx_whois.dtExpires)
        if(isExpired())
        {
            MenuItem[] miExpired;
            miExpired.push(MenuItem("Claim",                   "", tvm.functionId(onExpired)     ));
            miExpired.push(MenuItem("Refresh Whois",           "", tvm.functionId(onRefreshWhois)));
            miExpired.push(MenuItem("Enter another DeNS name", "", tvm.functionId(mainMenu)      ));

            Menu.select(format("Domain ({}) expired! You can claim it.", ctx_name), "", miExpired);
        }
        else 
        {
            MenuItem[] miActive;
            miActive.push(MenuItem("Manage domain",           "", tvm.functionId(onActive)      ));
            miActive.push(MenuItem("Refresh Whois",           "", tvm.functionId(onRefreshWhois)));
            miActive.push(MenuItem("Enter another DeNS name", "", tvm.functionId(mainMenu)      ));

            Menu.select("Enter your choice: ", "", miActive);
        }
    }

    //========================================
    //
    function onExpired(uint32 index) public
    {
        index = 0;
        AddressInput.get(tvm.functionId(onMsigEnter), "Enter owner wallet: ");  
    }

    //========================================
    //
    function onActive(uint32 index) public
    {
        index = 0;
        MenuItem[] mi;
        if (canProlongate()) {               
            mi.push(MenuItem("Prolong domain", "", tvm.functionId(onManageProlong)));
        }          
        mi.push(MenuItem("Change Endpoint",           "", tvm.functionId(onManageEndpoint)));
        mi.push(MenuItem("Change Owner",              "", tvm.functionId(onManageOwner)   ));
        mi.push(MenuItem("Change Registration Type",  "", tvm.functionId(onManageRegType) ));
        mi.push(MenuItem("Change Registration Price", "", tvm.functionId(onManageRegPrice)));
        mi.push(MenuItem("Change Comment",            "", tvm.functionId(onManageComment) )); 
        mi.push(MenuItem("Refresh Whois",             "", tvm.functionId(onAddressCheck)  ));                                 
        mi.push(MenuItem("Enter another DeNS name",   "", tvm.functionId(mainMenu)        ));

        Menu.select("Enter your choice: ", "", mi);
    }

    //========================================
    //
    function onRefreshWhois  (uint32 index) public {    index = 0;    onPathEnter(ctx_name);                                                                             } // Full refresh, refreshes account state AND whois, is needed after deployment
    function onManageEndpoint(uint32 index) public {    index = 0;    AddressInput.get(tvm.functionId(onChangeEndpoint), "Enter new endpoint: "                    );    }
    function onManageOwner   (uint32 index) public {    index = 0;    AddressInput.get(tvm.functionId(onChangeOwner),    "Enter new owner: "                       );    }
    function onManageRegPrice(uint32 index) public {    index = 0;    AmountInput.get (tvm.functionId(onChangePrice),    "Enter new price: ", 9, 1, 999999999999999);    }
    function onManageComment (uint32 index) public {    index = 0;    Terminal.input  (tvm.functionId(onChangeComment),  "Enter new comment: ", false              );    }

    function onManageRegType (uint32 index) public
    {
        index = 0;
        Terminal.print(0, "(0) FFA; (1) MONEY; (2) OWNER; (3) DENY.");
        AmountInput.get(tvm.functionId(onChangeRegType),  "Enter new type (0-3): ", 0, 0, 3);
    }

    function onManageProlong(uint32 index) public view
    {
        index = 0;        
        TvmCell body = tvm.encodeBody(IDnsRecord.prolongate);
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);       
    }                    

    //========================================
    //
    function onChangeEndpoint(address value) public 
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.changeEndpointAddress, value);
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(0);
    }      

    //========================================
    //
    function onChangeOwner(address value) public 
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.changeOwner, value);
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(0);
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
        onAddressCheck(0);
    }

    //========================================
    //
    function onChangePrice(int256 value) public
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.changeRegistrationPrice, uint128(value));
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(0);
    }     

    //========================================
    //
    function onChangeComment(string value) public
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.changeComment, value);
        _sendTransact(ctx_whois.ownerAddress, ctx_domain, body, 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(0);
    }            

    //========================================
    //
    function onClaimExpired(int256 value) public
    {
        TvmCell body = tvm.encodeBody(IDnsRecord.claimExpired, msigAddress, true);
        _sendTransact(msigAddress, ctx_domain, body, uint128(value) + 0.5 ton);

        // reload whois and show it one more time
        onAddressCheck(0);
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