import hashlib
import base64

import requests

from .interfaces import Responder, ErrorCode, LedgerType
    
# Responder implementation
class KSIResponder(Responder):
    """
    KSI Implementation of the Responder.
    """
    
    def __init__(self, url: str, hash_algorithm: str, username: str, password: str):
        """Initializes the KSIResponder
        :param str url: URL for Catena signatures API
        :param str hash_algorithm: Hash algorithm to use 
        :param str username: Username for Catena service
        :param str password: Password for Catena service
        """
        self.url = url
        
        if hash_algorithm in {"SHA-1", "SHA-256", "SHA-384", "SHA-512", "RIPEMD160"}:
            self.hash_algorithm = hash_algorithm
        else: # TODO, better error handling
            print("ERROR: hash algorithm:", hash_algorithm, "not supported, exiting")
            exit(1)
        self.username = username
        self.password = password
        self.ledger_type = LedgerType.KSI
    
    async def send_data(self, nonce: str, data: bytes) -> bool:
        """Hashes data and sends the hash to KSI Catena service.
        Catena returns the associated KSI signature, which will be returned as tx_hash.
        
        :param string nonce: the identifier to be unique inside interledger for a data item
        :param bytes data: data to be hashed
        
        :returns: True if the operation goes well; False otherwise
        :rtype: dict {
            'status': bool,
            'tx_hash': str,     # which is KSI id in this case
            'exception': object,# only with errors
            'error_code': Enum, # only with errors
            'message': str      # only with errors
        }
        
        """
        
        # calculate Base64 encoded hash over data
        if self.hash_algorithm == "SHA-1":
            h = hashlib.sha1()
        elif self.hash_algorithm == "SHA-256":
            h = hashlib.sha256()
        elif self.hash_algorithm == "SHA-384":
            h = hashlib.sha384()
        elif self.hash_algorithm == "SHA-512":
            h = hashlib.sha512()
        elif self.hash_algorithm == "RIPEMD160":
            # TODO: RIPEMD160 may not be supported on all systems, catch exception here
            h = hashlib.new("ripemd160")

        else: # should not happen
            return {"status": False, 
                    "error_code": ErrorCode.UNSUPPORTED_KSI_HASH,
                    "message": "Wrong KSI hash algorithm",
                    "tx_hash": ""}
        
        h.update(data)
        hash_value = base64.b64encode(h.digest()).decode('ascii')
        
        # Create a KSI Catena request
        request = {}
        request['dataHash'] = {}
        request['dataHash']['algorithm'] = self.hash_algorithm
        request['dataHash']['value'] = hash_value
        request['level'] = 0
        request['metadata'] = {}
        
        # send it as a POST request and check for the result
        ksi_request = requests.post(self.url, json=request, auth=(self.username, self.password))
        
        if ((ksi_request.status_code == 200) and 
                (ksi_request.json()['details']['dataHash'] == request['dataHash']) and 
                (ksi_request.json()['verificationResult']['status'] == "OK")):

            # request was successful, return the id
            return {"status": True,
                    "tx_hash": ksi_request.json()['id']}
        
        else: # some error happened
            return {"status": False, 
                    "error_code": ErrorCode.TRANSACTION_FAILURE,
                    "message": ksi_request.json(),
                    "tx_hash": ""}
