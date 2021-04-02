# freeton_dens_v2

# Running the tests

```
cd tests
./run_tests.py http://192.168.0.80
```

Here `http://192.168.0.80` is the address of local node of `TON OS SE`.

Possible arguments:

`--disable-giver` - by default Giver for `TON OS SE` is used; However, if you want to test the script on DEV, you can use this flag, however, you will do all account top-ups manyally;

`--throw` - by default tests will suppress all the errors and get only error codes from them, because for some tests getting an error code is actually a successfull execution. If you want to force and see errors as-is, use this flag;