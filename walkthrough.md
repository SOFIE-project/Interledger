
#### Walkthrough

This is the step list, present and future, guiding the implementation of the Interledger component.

- [X] **Step 1:** 
    - Write a version of the component assuming no transaction failures and network errors;
    - Create working version for Ethereum;
    - Simple data storage with lists;

- [ ] **Step 2:** 
    - Write CLI application for interactive testing;
    - Store data (e.g. asset states) in a local DB for recovery;
    - Handle transaction failures on the Responder;

- [ ] **Step 3:** 
    - Handle transaction failures on the Inititator;
    - Retry sending transactions;

- [ ] **Step 4:** 
    - Recovery from failure / restart;
    - Retry on timeout;
    - Support other ledgers;