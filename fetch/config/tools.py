tools = [
    {
        "type": "function",
        "function": {
            "name": "help",
            "description": "Gets help with the agent.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_coin_price",
            "description": "Gets the price of a given coin type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_type": {"type": "string"},
                    "amount": {"type": "number"}
                },
            },
            "required": ["coin_type", "amount"],
            "additionalProperties": False
        },
        "strict": True
    },
    {
        "type": "function",
        "function": {
            "name": "get_bitcoin_address",
            "description": "Gets the bitcoin address of the user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ethereum_address",
            "description": "Gets the ethereum address of the user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_solana_address",
            "description": "Gets the solana address of the user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_icp_address",
            "description": "Gets the ICP address of the user.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_bitcoin_balance",
            "description": "Gets the balance of a given coin type.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ethereum_balance",
            "description": "Gets the balance of a given coin type.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_solana_balance",
            "description": "Gets the balance of a given coin type.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_icp_balance",
            "description": "Gets the balance of ICP.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_solana",
            "description": "Sends solana coin from my wallet to a specified address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinationAddress": {
                        "type": "string",
                        "description": "The destination solana address."
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to send in solana."
                    }
                },
                "required": ["destinationAddress", "amount"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_icp",
            "description": "Sends ICP from my wallet to a specified address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinationAddress": {
                        "type": "string",
                        "description": "The destination ICP address / principal."
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to send in ICP."
                    }
                },
                "required": ["destinationAddress", "amount"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_bitcoin",
            "description": "Sends bitcoin coin from my wallet to a specified address.",
            "parameters": {
                "type": "object",
                "properties": { 
                    "destinationAddress": {
                        "type": "string",
                        "description": "The destination bitcoin address."
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to send in bitcoin."
                    }
                },
                "required": ["destinationAddress", "amount"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_ethereum",
            "description": "Sends ethereum coin from my wallet to a specified address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinationAddress": {
                        "type": "string",
                        "description": "The destination ethereum address."
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to send in ethereum."
                    }
                },
                "required": ["destinationAddress", "amount"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_icp",
            "description": "Sends ICP from my wallet to a specified address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinationAddress": {
                        "type": "string",
                        "description": "The destination ICP address."
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to send in ICP."
                    }
                },
                "required": ["destinationAddress", "amount"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
]