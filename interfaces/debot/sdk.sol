pragma ton-solidity >= 0.38.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
interface ISdk 
{
    // Account info
    function getBalance        (uint32 answerId, address addr)                         external returns (uint128 nanotokens);
    function getAccountType    (uint32 answerId, address addr)                         external returns (int8    acc_type  );
    function getAccountCodeHash(uint32 answerId, address addr)                         external returns (uint256 code_hash );
    // Crypto
    function chacha20          (uint32 answerId, bytes data, bytes nonce, uint256 key) external returns (bytes   output    );
    // Crypto utils
    function signHash          (uint32 answerId, uint256 hash)                         external returns (bytes   arg1      );
    function genRandom         (uint32 answerId, uint32 length)                        external returns (bytes   buffer    );
    // 7z
    function compress7z        (uint32 answerId, bytes uncompressed)                   external returns (bytes   comp      );
    function uncompress7z      (uint32 answerId, bytes compressed)                     external returns (bytes   uncomp    );
}

//================================================================================
//
library Sdk 
{
	uint256 constant ID       = 0x8fc6454f90072c9f1f6d3313ae1608f64f4a0660c6ae9f42c68b6a79e2a1bc4b;
	int8    constant DEBOT_WC = -31;
    address constant a        = address.makeAddrStd(DEBOT_WC, ID);

	//========================================
    // Account info
    function getBalance        (uint32 answerId, address addr)                         public pure {    ISdk(a).getBalance        (answerId, addr);                }
	function getAccountType    (uint32 answerId, address addr)                         public pure {    ISdk(a).getAccountType    (answerId, addr);                }
	function getAccountCodeHash(uint32 answerId, address addr)                         public pure {    ISdk(a).getAccountCodeHash(answerId, addr);                }
    // Crypto
    function chacha20          (uint32 answerId, bytes data, bytes nonce, uint256 key) public pure {    ISdk(a).chacha20          (answerId, data, nonce, key);    }
    // Crypto utils
    function signHash          (uint32 answerId, uint256 hash)                         public pure {    ISdk(a).signHash          (answerId, hash);                }
	function genRandom         (uint32 answerId, uint32 length)                        public pure {    ISdk(a).genRandom         (answerId, length);              }
    // 7z
    function compress7z        (uint32 answerId, bytes uncompressed)                   public pure {    ISdk(a).compress7z        (answerId, uncompressed);        }
	function uncompress7z      (uint32 answerId, bytes compressed)                     public pure {    ISdk(a).uncompress7z      (answerId, compressed);          }

}

//================================================================================
//
