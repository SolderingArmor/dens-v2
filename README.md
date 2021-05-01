# Description

Please visit https://freeton.domains/about for general info.

# General information about deployment

Please visit https://freeton.domains/about for general info.

# Manual deployment

Requirements: `ton-client-py` python library.

Please check `tests/manual_deployment.py` example.

Don't run it "as is", rather understand the syntax and change the script as you want.\

```
cd tests
./manual_deployment.py
```

# General information about claiming

Please visit https://freeton.domains/about for general info.

# Running the tests

Requirements: `ton-client-py` python library.

```
cd tests
./run_tests.py http://localhost
```

Here `http://localhost` is the address of local node of `TON OS SE`.

Possible arguments:

`--disable-giver` - by default Giver for `TON OS SE` is used; However, if you want to test the script on DEV, you can use this flag, thus, you will have to do all account top-ups manually;

`--throw` - by default tests will suppress all the errors and get only error codes from them, because for some tests getting an error code is actually a successfull execution. If you want to force and see errors as-is, use this flag;

`--msig-giver=000.json` - use SetcodeMultisig instead of `TON OS SE` giver;