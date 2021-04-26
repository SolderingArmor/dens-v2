pragma ton-solidity >=0.42.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
interface ITerminal 
{
	function inputStr    (uint32 answerId, string prompt, bool multiline) external returns (string  value);
	function inputInt    (uint32 answerId, string prompt)                 external returns (int256  value);
	function inputUint   (uint32 answerId, string prompt)                 external returns (uint256 value);
	function inputTons   (uint32 answerId, string prompt)                 external returns (uint128 value);
	function inputBoolean(uint32 answerId, string prompt)                 external returns (bool    value);
	function print       (uint32 answerId, string message)                external;
	function printf      (uint32 answerId, string fmt, TvmCell fargs)     external;
}

library Terminal 
{
	uint256 constant ID       = 0x8796536366ee21852db56dccb60bc564598b618c865fc50c8b1ab740bba128e3;
	int8    constant DEBOT_WC = -31;
    address constant addr     = address.makeAddrStd(DEBOT_WC, ID);

	function inputStr    (uint32 answerId, string prompt, bool multiline) public pure {    ITerminal(addr).inputStr    (answerId, prompt, multiline);    }
	function inputInt    (uint32 answerId, string prompt)                 public pure {    ITerminal(addr).inputInt    (answerId, prompt);               }
	function inputUint   (uint32 answerId, string prompt)                 public pure {    ITerminal(addr).inputUint   (answerId, prompt);               }
	function inputTons   (uint32 answerId, string prompt)                 public pure {    ITerminal(addr).inputTons   (answerId, prompt);               }
	function inputBoolean(uint32 answerId, string prompt)                 public pure {    ITerminal(addr).inputBoolean(answerId, prompt);               }
	function print       (uint32 answerId, string message)                public pure {    ITerminal(addr).print       (answerId, message);              }
	function printf      (uint32 answerId, string fmt, TvmCell fargs)     public pure {    ITerminal(addr).printf      (answerId, fmt, fargs);           }
}

//================================================================================
//