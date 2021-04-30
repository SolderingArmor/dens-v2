pragma ton-solidity >= 0.42.0;
pragma AbiHeader time;
pragma AbiHeader pubkey;
pragma AbiHeader expire;

//================================================================================
//
interface ISdk 
{
    // Account info
    function getBalance                  (uint32 answerId, address addr)                         external returns (uint128 nanotokens);
    function getAccountType              (uint32 answerId, address addr)                         external returns (int8 acc_type);
    function getAccountCodeHash          (uint32 answerId, address addr)                         external returns (uint256 code_hash);
    //crypto 
    function chacha20                    (uint32 answerId, bytes data, bytes nonce, uint256 key) external returns (bytes output);
    //crypto utils
    function signHash                    (uint32 answerId, uint256 hash)                         external returns (bytes arg1);
    function genRandom                   (uint32 answerId, uint32 length)                        external returns (bytes buffer);
    //7z
    function compress7z                  (uint32 answerId, bytes uncompressed)                   external returns (bytes comp);
    function uncompress7z                (uint32 answerId, bytes compressed)                     external returns (bytes uncomp);
    //keys
    function mnemonicFromRandom          (uint32 answerId, uint32 dict, uint32 wordCount)        external returns (string phrase);
    function mnemonicVerify              (uint32 answerId, string phrase)                        external returns (bool valid);
    function mnemonicDeriveSignKeys      (uint32 answerId, string phrase, string path)           external returns (uint256 pub, uint256 sec);
    //hdkey
    function hdkeyXprvFromMnemonic       (uint32 answerId, string phrase)                                   external returns (string xprv);
    function hdkeyDeriveFromXprv         (uint32 answerId, string inXprv, uint32 childIndex, bool hardened) external returns (string xprv);
    function hdkeyDeriveFromXprvPath     (uint32 answerId, string inXprv, string path)                      external returns (string xprv);
    function hdkeySecretFromXprv         (uint32 answerId, string xprv)                                     external returns (uint256 sec);
    function hdkeyPublicFromXprv         (uint32 answerId, string xprv)                                     external returns (uint256 pub);
    function naclSignKeypairFromSecretKey(uint32 answerId, uint256 secret)                                  external returns (uint256 sec, uint256 pub);
    //string
    function substring                   (uint32 answerId, string str, uint32 start, uint32 count)          external returns (string substr);
    //sc
    function naclBox                     (uint32 answerId, bytes decrypted, bytes nonce, uint256 publicKey, uint256 secretKey) external returns (bytes encrypted);
    function naclBoxOpen                 (uint32 answerId, bytes encrypted, bytes nonce, uint256 publicKey, uint256 secretKey) external returns (bytes decrypted);
    function naclKeypairFromSecret       (uint32 answerId, uint256 secret)                                                     external returns (uint256 publicKey, uint256 secretKey);
    //query
    struct AccData 
    {
        address id;
        TvmCell data;
    }
    function getAccountsDataByHash(uint32 answerId, uint256 codeHash, address gt) external returns (AccData[] accDatas);
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
    function getBalance                  (uint32 answerId, address addr)                                    public pure {    ISdk(a).getBalance                  (answerId, addr);                          }
	function getAccountType              (uint32 answerId, address addr)                                    public pure {    ISdk(a).getAccountType              (answerId, addr);                          }
	function getAccountCodeHash          (uint32 answerId, address addr)                                    public pure {    ISdk(a).getAccountCodeHash          (answerId, addr);                          }
    // Crypto
    function chacha20                    (uint32 answerId, bytes data, bytes nonce, uint256 key)            public pure {    ISdk(a).chacha20                    (answerId, data, nonce, key);              }
    // Crypto utils
    function signHash                    (uint32 answerId, uint256 hash)                                    public pure {    ISdk(a).signHash                    (answerId, hash);                          }
	function genRandom                   (uint32 answerId, uint32 length)                                   public pure {    ISdk(a).genRandom                   (answerId, length);                        }
    // 7z
    function compress7z                  (uint32 answerId, bytes uncompressed)                              public pure {    ISdk(a).compress7z                  (answerId, uncompressed);                  }
	function uncompress7z                (uint32 answerId, bytes compressed)                                public pure {    ISdk(a).uncompress7z                (answerId, compressed);                    }
    //keys
    function mnemonicFromRandom          (uint32 answerId, uint32 dict, uint32 wordCount)                   public pure {    ISdk(a).mnemonicFromRandom          (answerId, dict, wordCount);               }
	function mnemonicVerify              (uint32 answerId, string phrase)                                   public pure {    ISdk(a).mnemonicVerify              (answerId, phrase);                        }
	function mnemonicDeriveSignKeys      (uint32 answerId, string phrase, string path)                      public pure {    ISdk(a).mnemonicDeriveSignKeys      (answerId, phrase, path);                  }
	//hdkey
	function hdkeyXprvFromMnemonic       (uint32 answerId, string phrase)                                   public pure {    ISdk(a).hdkeyXprvFromMnemonic       (answerId, phrase);                        }
	function hdkeyDeriveFromXprv         (uint32 answerId, string inXprv, uint32 childIndex, bool hardened) public pure {    ISdk(a).hdkeyDeriveFromXprv         (answerId, inXprv, childIndex, hardened);  }
	function hdkeyDeriveFromXprvPath     (uint32 answerId, string inXprv, string path)                      public pure {    ISdk(a).hdkeyDeriveFromXprvPath     (answerId, inXprv, path);                  }
	function hdkeySecretFromXprv         (uint32 answerId, string xprv)                                     public pure {    ISdk(a).hdkeySecretFromXprv         (answerId, xprv);                          }
	function hdkeyPublicFromXprv         (uint32 answerId, string xprv)                                     public pure {    ISdk(a).hdkeyPublicFromXprv         (answerId, xprv);                          }
	function naclSignKeypairFromSecretKey(uint32 answerId, uint256 secret)                                  public pure {    ISdk(a).naclSignKeypairFromSecretKey(answerId, secret);                        }
    //string
	function substring                   (uint32 answerId, string str, uint32 start, uint32 count)          public pure {    ISdk(a).substring(answerId, str, start, count);                                }
    //sc
	function naclBox                     (uint32 answerId, bytes decrypted, bytes nonce, uint256 publicKey, uint256 secretKey) public pure {    ISdk(a).naclBox(answerId, decrypted, nonce, publicKey, secretKey);      }
	function naclBoxOpen                 (uint32 answerId, bytes decrypted, bytes nonce, uint256 publicKey, uint256 secretKey) public pure {    ISdk(a).naclBoxOpen(answerId, decrypted, nonce, publicKey, secretKey);  }
	function naclKeypairFromSecret       (uint32 answerId, uint256 secret)                                  public pure {    ISdk(a).naclKeypairFromSecret(answerId, secret);                               }
    //query
	function getAccountsDataByHash       (uint32 answerId, uint256 codeHash, address gt)                    public pure {    ISdk(a).getAccountsDataByHash(answerId, codeHash, gt);                         }
}

//================================================================================
//
