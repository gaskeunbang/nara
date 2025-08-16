import os
import json
import requests
from enum import Enum
from datetime import datetime, timezone
from uuid import uuid4
from services.canister_service import make_canister
from services.coin_service import to_amount, to_smallest
from decimal import Decimal
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    StartSessionContent,
)
from uagents import Agent, Context, Protocol, Model
from uagents.experimental.quota import QuotaProtocol, RateLimit
from services.identity_service import generate_ed25519_principal

# ASI1 API settings
ASI1_API_KEY = os.getenv("ASI1_API_KEY")
ASI1_BASE_URL = "https://api.asi1.ai/v1"
ASI1_HEADERS = {
    "Authorization": f"Bearer {ASI1_API_KEY}",
    "Content-Type": "application/json"
}

# Setup agent
AGENT_NAME = 'Nara Wallet Agent'
agent = Agent(
    name=AGENT_NAME,
    seed="nara-wallet-agent",
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)

# Setup protocols
chat_proto = Protocol(spec=chat_protocol_spec)
health_protocol = QuotaProtocol(
    storage_reference=agent.storage, name="HealthProtocol", version="0.1.0"
)

# Setup tools
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
            "name": "generate_wallet_address",
            "description": "Generates a new wallet address for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_type": {"type": "string", "enum": ["BTC", "ETH", "SOL"]}
                },
                "required": ["coin_type"],
                "additionalProperties": False
            },
            "strict": True
        }
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
]

help_message = """
    Hello! 👋 I’m **Nara**, your AI Crypto Wallet Agent.

    I help you manage and grow your crypto portfolio by:
    1️⃣ Generating new wallet addresses for BTC, ETH, and SOL.
    2️⃣ Sending crypto to any valid blockchain address.
    3️⃣ Receiving crypto through your personal wallet address.
    4️⃣ Checking your real-time coin balances.
    5️⃣ Buying crypto instantly with secure Stripe payments.
    6️⃣ Getting the best conversion rates with AI-powered price comparison across markets.

    💬 You can simply chat with me to:
    - Create a new wallet address.
    - Transfer coins to another address.
    - Check your wallet balance.
    - Buy crypto using fiat currency.
    - Find the best market price for your coins.

    🔐 Every transaction is fast, secure, and stored on-chain.
"""


def unwrap_candid(value):
    v = value
    # Unwrap list/tuple satu elemen berulang kali
    while isinstance(v, (list, tuple)) and len(v) == 1:
        v = v[0]
    # Unwrap Result
    if isinstance(v, dict):
        if "Ok" in v:
            return v["Ok"]
        if "Err" in v:
            raise Exception(f"Canister returned error: {v['Err']}")
    return v


def get_private_key_for_sender(ctx: Context, sender: str):
    identities = ctx.storage.get("identity") or []
    if not isinstance(identities, list):
        identities = [identities]
    for item in identities:
        if isinstance(item, dict) and item.get("sender") == sender:
            return item.get("private_key")
    return None

async def call_icp_endpoint(ctx: Context, func_name: str, args: dict):
    ctx.logger.info(f"Calling ICP canister endpoint: {func_name} with arguments: {args}")
    # Create canister
    wallet_canister = make_canister("wallet", get_private_key_for_sender(ctx, getattr(ctx, "sender", "")))
    ctx.logger.info(f"Function {func_name}")

    try:
        if func_name == "help":
            result = help_message

        elif func_name == "generate_wallet_address":
            if args["coin_type"] == "BTC":
                result = wallet_canister.bitcoin_address(ctx.sender)
            elif args["coin_type"] == "ETH":
                result = wallet_canister.ethereum_address(ctx.sender)
            elif args["coin_type"] == "SOL":
                result = wallet_canister.solana_address()
            else:
                raise ValueError(f"Unsupported coin type: {args['coin_type']}")
                
        elif func_name == "get_balance":
            if args["coin_type"] == "BTC":
                address = wallet_canister.bitcoin_address(ctx.sender)
                result = wallet_canister.bitcoin_balance(address)
            elif args["coin_type"] == "ETH":
                address = wallet_canister.ethereum_address(ctx.sender)
                result = wallet_canister.ethereum_balance(address)
            elif args["coin_type"] == "SOL":
                address = wallet_canister.solana_address(ctx.sender)
                result = wallet_canister.solana_balance(address)
            else:
                raise ValueError(f"Unsupported coin type: {args['coin_type']}")

        elif func_name == "get_bitcoin_balance":
            address_raw = wallet_canister.bitcoin_address()
            address = unwrap_candid(address_raw)
            raw_balance = wallet_canister.bitcoin_balance(address)  # satoshi
            balance = unwrap_candid(raw_balance)
            result = to_amount("BTC", balance)
        elif func_name == "get_ethereum_balance":
            address_raw = wallet_canister.ethereum_address()
            address = unwrap_candid(address_raw)
            raw_balance = wallet_canister.ethereum_balance(address)  # wei (string)
            balance = unwrap_candid(raw_balance)
            result = to_amount("ETH", balance)
        elif func_name == "get_solana_balance":
            address_raw = wallet_canister.solana_address()
            address = unwrap_candid(address_raw)
            raw_balance = wallet_canister.solana_balance(address)  # lamports (Nat)
            balance = unwrap_candid(raw_balance)
            result = to_amount("SOL", balance)

        elif func_name == "get_bitcoin_address":
            result = unwrap_candid(wallet_canister.bitcoin_address())
        elif func_name == "get_ethereum_address":
            result = unwrap_candid(wallet_canister.ethereum_address())
        elif func_name == "get_solana_address":
            result = unwrap_candid(wallet_canister.solana_address())



        elif func_name == "send_solana":
            amount_value = args["amount"]
            if isinstance(amount_value, float):
                amount_value = Decimal(str(amount_value))
            amount_lamports = to_smallest("SOL", amount_value)  # int lamports
            result = wallet_canister.solana_send(args["destinationAddress"], amount_lamports)
        elif func_name == "send_ethereum":
            amount_value = args["amount"]
            if isinstance(amount_value, float):
                amount_value = Decimal(str(amount_value))
            amount_wei = to_smallest("ETH", amount_value)  # int wei
            result = wallet_canister.ethereum_send(args["to"], amount_wei)
        elif func_name == "send_bitcoin":
            amount_value = args["amount"]
            if isinstance(amount_value, float):
                amount_value = Decimal(str(amount_value))
            amount_satoshi = to_smallest("BTC", amount_value)  # int satoshi
            result = wallet_canister.bitcoin_send({"destination_address": args["to"], "amount_in_satoshi": amount_satoshi})

        else:
            raise ValueError(f"Unsupported function call: {func_name}")
        
        return result
    except Exception as e:
        raise Exception(f"ICP canister call failed: {str(e)}")

async def process_query(query: str, ctx: Context) -> str:
    try:
        # Step 1: Initial call to ASI1 with user query and tool
        user_message = {
            "role": "user",
            "content": query
        }
        payload = {
            "model": "asi1-mini",
            "messages": [user_message],
            "tools": tools,
            "temperature": 0.2,
            "max_tokens": 1024
        }
        response = requests.post(
            f"{ASI1_BASE_URL}/chat/completions",
            headers=ASI1_HEADERS,
            json=payload
        )
        response.raise_for_status()
        response_json = response.json()

        ctx.logger.info(f"Response: {response_json}")

        # Step 2: Parse tool calls from response
        tool_calls = response_json["choices"][0]["message"].get("tool_calls", [])
        messages_history = [user_message, response_json["choices"][0]["message"]]

        if not tool_calls:
            return f"""I couldn't determine your request. I'm Nara, your AI Crypto Wallet Agent, and I can help you with tasks such as generating new wallet addresses for BTC, ETH, and SOL, sending crypto to any valid blockchain address, receiving crypto through your personal wallet address, checking your real-time coin balances, buying crypto instantly with secure Stripe payments, and finding the best conversion rates using AI-powered price comparison across markets. If your question is outside these areas, I won't be able to help, so please rephrase your question to match one of these topics."""

        # Step 3: Execute tools and format results
        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            tool_call_id = tool_call["id"]

            ctx.logger.info(f"Executing {func_name} with arguments: {arguments}")

            try:
                result = await call_icp_endpoint(ctx, func_name, arguments)
                content_to_send = json.dumps(result)
            except Exception as e:
                ctx.logger.error(f"Error executing tool: {str(e)}")
                error_content = {
                    "error": f"Tool execution failed: {str(e)}",
                    "status": "failed"
                }
                content_to_send = json.dumps(error_content)

            tool_result_message = {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": content_to_send
            }
            messages_history.append(tool_result_message)

        # Step 4: Send results back to ASI1 for final answer
        final_payload = {
            "model": "asi1-mini",
            "messages": messages_history,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        final_response = requests.post(
            f"{ASI1_BASE_URL}/chat/completions",
            headers=ASI1_HEADERS,
            json=final_payload
        )
        final_response.raise_for_status()
        final_response_json = final_response.json()

        # Step 5: Return the model's final answer
        return final_response_json["choices"][0]["message"]["content"]

    except Exception as e:
        ctx.logger.error(f"Error processing query: {str(e)}")
        return f"An error occurred while processing your request: {str(e)}"

@chat_proto.on_message(model=ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    try:
        ctx.sender = sender

        # send the acknowledgement for receiving the message
        ack = ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id
        )
        await ctx.send(sender, ack)

        for item in msg.content:
            if isinstance(item, StartSessionContent):
                ctx.logger.info(f"Got a start session message from {sender}")

                principal, pub_pem, priv_pem = generate_ed25519_principal()

                identities = ctx.storage.get("identity") or []
                if not isinstance(identities, list):
                    identities = [identities]

                already_exists = any(
                    isinstance(item, dict) and item.get("sender") == sender
                    for item in identities
                )

                if already_exists:
                    ctx.logger.info(f"Identity already exists for {sender}")
                    continue

                identities.append({
                    "principal": principal,
                    "public_key": pub_pem,
                    "private_key": priv_pem,
                    "sender": sender
                })
                ctx.storage.set("identity", identities)

                continue
            elif isinstance(item, TextContent):
                response_text = await process_query(item.text, ctx)
                ctx.logger.info(f"Response text: {response_text}")
                response = ChatMessage(
                    timestamp=datetime.now(timezone.utc),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=response_text)]
                )
                await ctx.send(sender, response)
            else:
                ctx.logger.info(f"Got unexpected content from {sender}")
    except Exception as e:
        ctx.logger.error(f"Error handling chat message: {str(e)}")
        error_response = ChatMessage(
            timestamp=datetime.now(timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=f"An error occurred: {str(e)}")]
        )
        await ctx.send(sender, error_response)

@chat_proto.on_message(model=ChatAcknowledgement)
async def handle_chat_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"[handle_chat_acknowledgement] Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")
    if msg.metadata:
        ctx.logger.info(f"Metadata: {msg.metadata}")

def agent_is_healthy() -> bool:
    """
    Implement the actual health check logic here.

    For example, check if the agent can connect to a third party API,
    check if the agent has enough resources, etc.
    """
    condition = True  # TODO: logic here
    return bool(condition)

class HealthCheck(Model):
    pass

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"

class AgentHealth(Model):
    agent_name: str
    status: HealthStatus

@health_protocol.on_message(HealthCheck, replies={AgentHealth})
async def handle_health_check(ctx: Context, sender: str, msg: HealthCheck):
    status = HealthStatus.UNHEALTHY
    try:
        if agent_is_healthy():
            status = HealthStatus.HEALTHY
    except Exception as err:
        ctx.logger.error(err)
    finally:
        await ctx.send(sender, AgentHealth(agent_name=AGENT_NAME, status=status))

# Attach protocols to agent
agent.include(health_protocol, publish_manifest=True)
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()