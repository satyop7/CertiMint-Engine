export const contractAddress = "0x5497D3d6aE886f709a7427B1f7f8DE0A2c715bCC"
export const abi = [
    {
        "name": "CreatedNFT",
        "inputs": [
            {
                "name": "tokenId",
                "type": "uint256",
                "indexed": true
            },
            {
                "name": "to",
                "type": "address",
                "indexed": true
            },
            {
                "name": "imageData",
                "type": "string",
                "indexed": false
            },
            {
                "name": "subject",
                "type": "string",
                "indexed": false
            },
            {
                "name": "course",
                "type": "string",
                "indexed": false
            }
        ],
        "anonymous": false,
        "type": "event"
    },
    {
        "name": "OwnershipTransferred",
        "inputs": [
            {
                "name": "previous_owner",
                "type": "address",
                "indexed": true
            },
            {
                "name": "new_owner",
                "type": "address",
                "indexed": true
            }
        ],
        "anonymous": false,
        "type": "event"
    },
    {
        "name": "RoleMinterChanged",
        "inputs": [
            {
                "name": "minter",
                "type": "address",
                "indexed": true
            },
            {
                "name": "status",
                "type": "bool",
                "indexed": false
            }
        ],
        "anonymous": false,
        "type": "event"
    },
    {
        "name": "Approval",
        "inputs": [
            {
                "name": "owner",
                "type": "address",
                "indexed": true
            },
            {
                "name": "approved",
                "type": "address",
                "indexed": true
            },
            {
                "name": "token_id",
                "type": "uint256",
                "indexed": true
            }
        ],
        "anonymous": false,
        "type": "event"
    },
    {
        "name": "ApprovalForAll",
        "inputs": [
            {
                "name": "owner",
                "type": "address",
                "indexed": true
            },
            {
                "name": "operator",
                "type": "address",
                "indexed": true
            },
            {
                "name": "approved",
                "type": "bool",
                "indexed": false
            }
        ],
        "anonymous": false,
        "type": "event"
    },
    {
        "name": "Transfer",
        "inputs": [
            {
                "name": "sender",
                "type": "address",
                "indexed": true
            },
            {
                "name": "receiver",
                "type": "address",
                "indexed": true
            },
            {
                "name": "token_id",
                "type": "uint256",
                "indexed": true
            }
        ],
        "anonymous": false,
        "type": "event"
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "owner",
        "inputs": [],
        "outputs": [
            {
                "name": "",
                "type": "address"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "balanceOf",
        "inputs": [
            {
                "name": "owner",
                "type": "address"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "ownerOf",
        "inputs": [
            {
                "name": "token_id",
                "type": "uint256"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "address"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "getApproved",
        "inputs": [
            {
                "name": "token_id",
                "type": "uint256"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "address"
            }
        ]
    },
    {
        "stateMutability": "payable",
        "type": "function",
        "name": "approve",
        "inputs": [
            {
                "name": "to",
                "type": "address"
            },
            {
                "name": "token_id",
                "type": "uint256"
            }
        ],
        "outputs": []
    },
    {
        "stateMutability": "nonpayable",
        "type": "function",
        "name": "setApprovalForAll",
        "inputs": [
            {
                "name": "operator",
                "type": "address"
            },
            {
                "name": "approved",
                "type": "bool"
            }
        ],
        "outputs": []
    },
    {
        "stateMutability": "payable",
        "type": "function",
        "name": "transferFrom",
        "inputs": [
            {
                "name": "owner",
                "type": "address"
            },
            {
                "name": "to",
                "type": "address"
            },
            {
                "name": "token_id",
                "type": "uint256"
            }
        ],
        "outputs": []
    },
    {
        "stateMutability": "payable",
        "type": "function",
        "name": "safeTransferFrom",
        "inputs": [
            {
                "name": "owner",
                "type": "address"
            },
            {
                "name": "to",
                "type": "address"
            },
            {
                "name": "token_id",
                "type": "uint256"
            }
        ],
        "outputs": []
    },
    {
        "stateMutability": "payable",
        "type": "function",
        "name": "safeTransferFrom",
        "inputs": [
            {
                "name": "owner",
                "type": "address"
            },
            {
                "name": "to",
                "type": "address"
            },
            {
                "name": "token_id",
                "type": "uint256"
            },
            {
                "name": "data",
                "type": "bytes"
            }
        ],
        "outputs": []
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "totalSupply",
        "inputs": [],
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "tokenByIndex",
        "inputs": [
            {
                "name": "index",
                "type": "uint256"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "tokenOfOwnerByIndex",
        "inputs": [
            {
                "name": "owner",
                "type": "address"
            },
            {
                "name": "index",
                "type": "uint256"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ]
    },
    {
        "stateMutability": "nonpayable",
        "type": "function",
        "name": "burn",
        "inputs": [
            {
                "name": "token_id",
                "type": "uint256"
            }
        ],
        "outputs": []
    },
    {
        "stateMutability": "nonpayable",
        "type": "function",
        "name": "permit",
        "inputs": [
            {
                "name": "spender",
                "type": "address"
            },
            {
                "name": "token_id",
                "type": "uint256"
            },
            {
                "name": "deadline",
                "type": "uint256"
            },
            {
                "name": "v",
                "type": "uint8"
            },
            {
                "name": "r",
                "type": "bytes32"
            },
            {
                "name": "s",
                "type": "bytes32"
            }
        ],
        "outputs": []
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "DOMAIN_SEPARATOR",
        "inputs": [],
        "outputs": [
            {
                "name": "",
                "type": "bytes32"
            }
        ]
    },
    {
        "stateMutability": "nonpayable",
        "type": "function",
        "name": "transfer_ownership",
        "inputs": [
            {
                "name": "new_owner",
                "type": "address"
            }
        ],
        "outputs": []
    },
    {
        "stateMutability": "nonpayable",
        "type": "function",
        "name": "renounce_ownership",
        "inputs": [],
        "outputs": []
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "name",
        "inputs": [],
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "symbol",
        "inputs": [],
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "isApprovedForAll",
        "inputs": [
            {
                "name": "arg0",
                "type": "address"
            },
            {
                "name": "arg1",
                "type": "address"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "is_minter",
        "inputs": [
            {
                "name": "arg0",
                "type": "address"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "bool"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "nonces",
        "inputs": [
            {
                "name": "arg0",
                "type": "uint256"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ]
    },
    {
        "stateMutability": "nonpayable",
        "type": "function",
        "name": "mintNFT",
        "inputs": [
            {
                "name": "base64_image",
                "type": "string"
            },
            {
                "name": "subject",
                "type": "string"
            },
            {
                "name": "course",
                "type": "string"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "uint256"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "tokenURI",
        "inputs": [
            {
                "name": "token_id",
                "type": "uint256"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "image_data",
        "inputs": [
            {
                "name": "arg0",
                "type": "uint256"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "subjects",
        "inputs": [
            {
                "name": "arg0",
                "type": "uint256"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ]
    },
    {
        "stateMutability": "view",
        "type": "function",
        "name": "courses",
        "inputs": [
            {
                "name": "arg0",
                "type": "uint256"
            }
        ],
        "outputs": [
            {
                "name": "",
                "type": "string"
            }
        ]
    },
    {
        "stateMutability": "nonpayable",
        "type": "constructor",
        "inputs": [],
        "outputs": []
    }
]