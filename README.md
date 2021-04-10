# Description

here

# How does it work?

here

# Tips and limitations

here

# Running the tests

```
cd tests
./run_tests.py http://localhost
```

Here `http://localhost` is the address of local node of `TON OS SE`.

Possible arguments:

`--disable-giver` - by default Giver for `TON OS SE` is used; However, if you want to test the script on DEV, you can use this flag, thus, you will have to do all account top-ups manually;

`--throw` - by default tests will suppress all the errors and get only error codes from them, because for some tests getting an error code is actually a successfull execution. If you want to force and see errors as-is, use this flag;

`--msig-giver=000.json` - use Multisig instead of `TON OS SE` giver;