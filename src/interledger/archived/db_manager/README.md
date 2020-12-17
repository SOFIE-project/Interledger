# DBManager

In order to implement a state recovery for Interledger, the status of the transactions will be stored in a DB. The python library used is [sqlalchemy](https://www.sqlalchemy.org/).

The class `DBManager` is in charge to create / update / delete and query entries in the DB.
The tables in the DB are two and each should store the required information for the asset transfer protocol of interledger. Every asset, in both ledgers, has the following information:
- Its id;
- Its state;
- Its owner.

For simplicity, the two tables should have equal length and equal stored ids. En fact, inserting a removing an entry will modify both the tables.
- [ ] **Future work:** evaluate if the two table could store a different set of asset ids. What happens when an asset with id *asset1* should be transfered from L1 to L2, but L2's table does not store *asset1*?
    - Do we consider it as "*asset1* not existing in L2*, and thus transfer is impossible?
    - Do we create an entry?

![DB](../../imgs/DBManager.png)