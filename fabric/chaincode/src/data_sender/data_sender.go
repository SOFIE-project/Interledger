package main

import (
	"encoding/json"
	"fmt"

	"github.com/hyperledger/fabric/core/chaincode/shim"
	"github.com/hyperledger/fabric/protos/peer"
)

// Event for sending data to another ledger
type InterledgerEventSending struct {
	Id   uint64
	Data string // bytes not allowed in chaincode, see https://github.com/hyperledger/fabric-contract-api-go/blob/master/tutorials/getting-started.md
}

// Interledger for data sender
type InterledgerSender interface {
	interledgerCommit()
	interledgerAbort()
}

// This is a sample contract as data sender used for develpment and testing
type DataSender struct{}

// Init is called during chaincode instantiation to initialize any
// data. Note that chaincode upgrade also calls this function to reset
// or to migrate data.
func (t *DataSender) Init(stub shim.ChaincodeStubInterface) peer.Response {
	_, args := stub.GetFunctionAndParameters()

	if len(args) != 0 {
		return shim.Error("Incorrect arguments. Expecting no arguments!")
	}

	// Store the key and value on the ledger by calling stub.PutState()
	id := 0
	payload, _ := json.Marshal(id)

	err := stub.PutState("id", payload)
	if err != nil {
		return shim.Error(fmt.Sprintf("Failed to create id: %s", args[0]))
	}
	return shim.Success(nil)
}

// Invoke is called per transaction on the chaincode.
func (t *DataSender) Invoke(stub shim.ChaincodeStubInterface) peer.Response {
	// Extract the function and args from the transaction proposal
	fn, args := stub.GetFunctionAndParameters()

	var result string
	var err error
	if fn == "emitData" {
		err = emitData(stub, args)
	} else if fn == "interledgerCommit" {
		err = interledgerCommit(stub, args)
	} else if fn == "interledgerAbort" {
		err = interledgerAbort(stub, args)
	}

	if err != nil {
		return shim.Error(err.Error())
	}

	result = "OK"
	return shim.Success([]byte(result))
}

// This is the application logic to emit data to another ledger via event, assumes the paramter below
// @param data1 encoded data content in byte string
func emitData(stub shim.ChaincodeStubInterface, args []string) error {
	var id1 uint64
	var data1 string

	// fetch id & data
	id_json, _ := stub.GetState("id")
	_ = json.Unmarshal(id_json, &id1)

	data1 = args[0]

	// package event
	id1 += 1
	iles := &InterledgerEventSending{
		Id:   id1,
		Data: data1}

	payload_event, _ := json.Marshal(iles)

	payload_id, _ := json.Marshal(id1)
	stub.PutState("id", payload_id)

	// emit event
	_ = stub.SetEvent("InterledgerEventSending", payload_event)

	return nil
}

// This is the function that will be called when the recipient has accepted the data, which assumes the following parameter
// @param id The identifier of data sending event
func interledgerCommit(stub shim.ChaincodeStubInterface, args []string) error {
	// Function that will be called when the recipient has accepted the data
	return nil
}

// This is the function that will be called when the recipient has rejected the data, or there have been an error.
// It assumes the following paramters
// @param id The identifier of data sending event
// @param reason The error code indicating the reason for failure
func interledgerAbort(stub shim.ChaincodeStubInterface, args []string) error {
	// Function that will be called when the recipient has rejected the data, or there have been an error.
	return nil
}

// main function starts up the chaincode in the container during instantiate
func main() {
	err := shim.Start(new(DataSender))
	if err != nil {
		fmt.Printf("Error starting chaincode: %s", err)
	}
}
