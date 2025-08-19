import json
import requests
from datetime import datetime, timezone
from uuid import uuid4
from decimal import Decimal
from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    StartSessionContent,
)
from uagents import Context, Protocol

# Utils
from utils.canister import make_canister
from utils.coin import to_amount, to_smallest
from utils.pricing import get_price_usd
from utils.identity import generate_ed25519_principal
from utils.candid import unwrap_candid
from utils.context import get_private_key_for_sender, get_principal_for_sender

# Config
from config.messages import help_message, welcome_message
from config.tools import tools
from config.settings import ASI1_BASE_URL, ASI1_HEADERS

async def get_crypto_price(ctx: Context, coin_type: str, amount_in_token: float):
    return get_price_usd(coin_type, amount_in_token, logger=ctx.logger)

async def call_endpoint(ctx: Context, func_name: str, args: dict):
    ctx.logger.info(f"Calling ICP canister endpoint: {func_name} with arguments: {args}")
    # Create canister
    wallet_canister = make_canister("wallet", get_private_key_for_sender(ctx))
    icp_ledger_canister = make_canister("icp_ledger", get_private_key_for_sender(ctx))
    ctx.logger.info(f"Function {func_name}")

    try:
        if func_name == "help":
            result = help_message

        elif func_name == "get_coin_price":
            result = await get_crypto_price(ctx, args["coin_type"], args["amount"])
            ctx.logger.info(f"Result: {result}")

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

        elif func_name == "get_icp_balance":
            raw_balance = icp_ledger_canister.icrc1_balance_of({"owner": get_principal_for_sender(ctx), "subaccount": []})
            e8s_value = unwrap_candid(raw_balance)
            result = to_amount("ICP", e8s_value)

        elif func_name == "get_bitcoin_address":
            result = unwrap_candid(wallet_canister.bitcoin_address())
        elif func_name == "get_ethereum_address":
            result = unwrap_candid(wallet_canister.ethereum_address())
        elif func_name == "get_solana_address":
            result = unwrap_candid(wallet_canister.solana_address())
        elif func_name == "get_icp_address":
            result = get_principal_for_sender(ctx)

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
            result = wallet_canister.ethereum_send(args["destinationAddress"], amount_wei)
        elif func_name == "send_bitcoin":
            amount_value = args["amount"]
            if isinstance(amount_value, float):
                amount_value = Decimal(str(amount_value))
            amount_satoshi = to_smallest("BTC", amount_value)  # int satoshi
            result = wallet_canister.bitcoin_send({"destination_address": args["destinationAddress"], "amount_in_satoshi": amount_satoshi})
        elif func_name == "send_icp":
            amount_value = args["amount"]
            if isinstance(amount_value, float):
                amount_value = Decimal(str(amount_value))
            amount_e8s = to_smallest("ICP", amount_value)  # int e8s

            destination = args["destinationAddress"]
            tx_res = icp_ledger_canister.icrc1_transfer({
                "to": {
                    "owner": destination,
                    "subaccount": None,
                },
                "amount": amount_e8s,
                "fee": None,
                "memo": None,
                "from_subaccount": None,
                "created_at_time": None,
            })
            result = unwrap_candid(tx_res)
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
            return welcome_message

        # Step 3: Execute tools and format results
        for tool_call in tool_calls:
            func_name = tool_call["function"]["name"]
            arguments = json.loads(tool_call["function"]["arguments"])
            tool_call_id = tool_call["id"]

            try:
                result = await call_endpoint(ctx, func_name, arguments)
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

chat_proto = Protocol(spec=chat_protocol_spec)

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
