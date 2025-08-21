#!/usr/bin/env python3
"""
Configuration file for the fetch project
Combines all configuration from the config/ folder
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==================== SETTINGS ====================

# Stripe Configuration
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_API_URL = os.getenv("STRIPE_API_URL", "https://api.stripe.com/v1")
STRIPE_WEBHOOK_URL = os.getenv("STRIPE_WEBHOOK_URL", "http://localhost:8000")

# ASI1 Configuration
ASI1_BASE_URL = os.getenv("ASI1_BASE_URL", "https://api.asi1.ai")
ASI1_API_KEY = os.getenv("ASI1_API_KEY")
ASI1_HEADERS = {
    "Authorization": f"Bearer {ASI1_API_KEY}",
    "Content-Type": "application/json"
}

# ==================== MESSAGES ====================

help_message = (
    "🤖 **Nara Wallet Agent** - Your AI-powered crypto wallet assistant!\n\n"
    "I can help you with:\n"
    "- Check your wallet balance.\n"
    "- Buy crypto using fiat currency.\n"
    "- Find the best market price for your coins.\n"
    "- Check your coin price.\n"
    "🔐 Every transaction is fast, secure, and stored on-chain.\n"
)

welcome_message = (
    "🚀 Welcome to Nara Wallet Agent!\n\n"
    "I'm your AI-powered crypto wallet assistant. I can help you:\n\n"
    "💰 **Check Balances** - View your BTC, ETH, SOL, and ICP balances\n"
    "🔍 **Get Addresses** - Retrieve your wallet addresses for any supported coin\n"
    "💱 **Buy Crypto** - Purchase crypto using fiat currency via Stripe\n"
    "📊 **Price Checks** - Get real-time prices for any supported cryptocurrency\n"
    "📤 **Send Tokens** - Transfer tokens to other addresses\n\n"
    "Just ask me what you'd like to do! For example:\n"
    "- 'What's my Bitcoin balance?'\n"
    "- 'I want to buy 0.001 BTC'\n"
    "- 'What's the current price of Ethereum?'\n"
    "- 'Send 0.1 ETH to 0x123...'\n\n"
    "Type 'help' anytime to see this message again."
)

# ==================== TOOLS ====================

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
            "name": "send_bitcoin",
            "description": "Sends bitcoin to a destination address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinationAddress": {"type": "string"},
                    "amount": {"type": "number"}
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
            "description": "Sends ethereum to a destination address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinationAddress": {"type": "string"},
                    "amount": {"type": "number"}
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
            "name": "send_solana",
            "description": "Sends solana to a destination address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinationAddress": {"type": "string"},
                    "amount": {"type": "number"}
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
            "description": "Sends ICP to a destination address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinationAddress": {"type": "string"},
                    "amount": {"type": "number"}
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
            "name": "buy_crypto",
            "description": "Buys crypto using fiat currency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coinType": {"type": "string"},
                    "amount": {"type": "number"}
                },
                "required": ["coinType", "amount"],
                "additionalProperties": False
            },
            "strict": True
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_stripe_checkout",
            "description": "Creates a Stripe checkout session for purchasing crypto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_type": {"type": "string"},
                    "destinationAddress": {"type": "string"},
                    "amount_usd": {"type": "number"}
                },
                "required": ["coin_type", "destinationAddress", "amount_usd"],
                "additionalProperties": False
            },
            "strict": True
        }
    }
]
