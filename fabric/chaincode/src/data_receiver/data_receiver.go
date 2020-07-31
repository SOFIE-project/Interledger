package main

import (
	"encoding/json"
	"fmt"
	"strconv"

	"github.com/hyperledger/fabric/core/chaincode/shim"
	"github.com/hyperledger/fabric/protos/peer"
)

// Event for signalling that the recipient has accepted the data
type InterledgerEventAccepted struct {
	Nonce uint64
}

// Event for signalling that the recipient has rejected the data
type InterledgerEventRejected struct {
	Nonce uint64
}

type DataItem struct {
	Nonce uint64
	Data  string // bytes not allowed in chaincode, see https://github.com/hyperledger/fabric-contract-api-go/blob/master/tutorials/getting-started.md
}

// Interledger for data receiver
type InterledgerReceiver interface {
	interledgerReceive() // Function to receive data from Interledger
}

// This is a sample contract as data sender used for develpment and testing
type DataReceiver struct{}

// Init is called during chaincode instantiation to initialize any
// data. Note that chaincode upgrade also calls this function to reset
// or to migrate data.
func (t *DataReceiver) Init(stub shim.ChaincodeStubInterface) peer.Response {
	_, args := stub.GetFunctionAndParameters()

	if len(args) != 0 {
		return shim.Error("Incorrect arguments. Expecting no arguments!")
	}

	var items []DataItem

	payload, _ := json.Marshal(items)
	err := stub.PutState("items", payload)

	if err != nil {
		return shim.Error(fmt.Sprintf(""))
	}
	return shim.Success(nil)
}

// Invoke is called per transaction on the chaincode.
func (t *DataReceiver) Invoke(stub shim.ChaincodeStubInterface) peer.Response {
	// Extract the function and args from the transaction proposal
	fn, args := stub.GetFunctionAndParameters()

	var result string
	var err error
	if fn == "interledgerReceive" {
		err = interledgerReceive(stub, args)
	}

	if err != nil {
		return shim.Error(err.Error())
	}

	result = "OK"
	return shim.Success([]byte(result))
}

// This is the function to receive data from Interledger, which assumes the following parameters to be passed.
// @param nonce The unique identifier of data event
// @param data The actual data content encoded in byte string
func interledgerReceive(stub shim.ChaincodeStubInterface, args []string) error {
	// Function to receive data from Interledger
	var nonce uint64
	var data string

	// fetch nonce & data
	nonce, _ = strconv.ParseUint(args[0], 10, 64)
	data = args[1]

	var items []DataItem

	items_json, _ := stub.GetState("items")
	_ = json.Unmarshal(items_json, &items)

	dataItem := &DataItem{
		Nonce: nonce,
		Data:  data}

	items = append(items, *dataItem)
	payload, _ := json.Marshal(items)
	stub.PutState("items", payload)

	// emit event
	nonce_bytes, _ := json.Marshal(nonce)
	_ = stub.SetEvent("InterledgerEventAccepted", nonce_bytes)

	return nil
}

// main function starts up the chaincode in the container during instantiate
func main() {
	if err := shim.Start(new(DataReceiver)); err != nil {
		fmt.Printf("Error starting chaincode: %s", err)
	}
}
