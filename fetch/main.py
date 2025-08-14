import os
import json
import requests
from enum import Enum
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

from ic.canister import Canister

from uagents_core.contrib.protocols.chat import (
    chat_protocol_spec,
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    StartSessionContent,
)
from uagents import Agent, Context, Protocol, Model
from uagents.experimental.quota import QuotaProtocol, RateLimit

# -----------------------------------------------------------------------------
# Ensure required environment variables are set before importing canister module
# -----------------------------------------------------------------------------
try:
    project_root_dir = Path(__file__).resolve().parents[1]
    canister_ids_path = project_root_dir / "canister_ids.json"

    # Default to local network if not explicitly provided
    dfx_network = os.getenv("DFX_NETWORK") or "local"
    os.environ.setdefault("DFX_NETWORK", dfx_network)

    # Load canister id for escrow from canister_ids.json if present
    if canister_ids_path.exists():
        with canister_ids_path.open("r") as f:
            canister_ids = json.load(f)
        escrow_ids = canister_ids.get("escrow", {}) if isinstance(canister_ids, dict) else {}
        canister_id_escrow = escrow_ids.get(dfx_network)
        if canister_id_escrow:
            os.environ.setdefault("CANISTER_ID_ESCROW", canister_id_escrow)

    # Point candid path to the repo's escrow.did by default
    default_candid_path = project_root_dir / "src" / "escrow" / "escrow.did"
    if default_candid_path.exists():
        os.environ.setdefault("CANISTER_CANDID_PATH_ESCROW", str(default_candid_path))
except Exception:
    # Do not block startup if best-effort env bootstrap fails; the canister
    # module will still raise clear errors if env is incomplete.
    pass

try:
    # When running from project root: `python -m fetch.main`
    from fetch.icp_canister import backend
except ModuleNotFoundError:
    # When running from inside fetch directory: `python main.py`
    from icp_canister import backend

# ASI1 API settings
ASI1_API_KEY = os.getenv("ASI1_API_KEY")
ASI1_BASE_URL = "https://api.asi1.ai/v1"
ASI1_HEADERS = {
    "Authorization": f"Bearer {ASI1_API_KEY}",
    "Content-Type": "application/json"
}

# Function definitions for ASI1 function calling
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
    }
]

help_message = """
Hello! 👋 I’m **Nara**, your AI Crypto Escrow Guardian.

I help you trade cryptocurrencies safely by:
1️⃣ Creating and managing token listings (for sellers).
2️⃣ Finding the best offers from various sellers (for buyers).
3️⃣ Securing funds in on-chain escrow until blockchain payment is confirmed.
4️⃣ Releasing assets only when all conditions are met.
5️⃣ Monitoring prices and detecting suspicious offers.

💬 You can simply chat with me to:
- Create a new listing.
- View available offers.
- Buy tokens from a listing.
- Check your transaction status.

🔒 Every process is transparent, fast, and secure across networks.
"""


async def call_icp_endpoint(ctx: Context, func_name: str, args: dict):
    ctx.logger.info(f"Calling ICP canister endpoint: {func_name} with arguments: {args}")
    try:
        if func_name == "help":
            result = help_message
        else:
            raise ValueError(f"Unsupported function call: {func_name}")
        
        return result
    except Exception as e:
        raise Exception(f"ICP canister call failed: {str(e)}")


async def process_query(query: str, ctx: Context) -> str:
    try:
        # Step 1: Initial call to ASI1 with user query and tools
        initial_message = {
            "role": "user",
            "content": query
        }
        payload = {
            "model": "asi1-mini",
            "messages": [initial_message],
            "tools": tools,
            "temperature": 0.7,
            "max_tokens": 1024
        }
        response = requests.post(
            f"{ASI1_BASE_URL}/chat/completions",
            headers=ASI1_HEADERS,
            json=payload
        )
        response.raise_for_status()
        response_json = response.json()

        # Step 2: Parse tool calls from response
        tool_calls = response_json["choices"][0]["message"].get("tool_calls", [])
        messages_history = [initial_message, response_json["choices"][0]["message"]]


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

AGENT_NAME = 'Nara Agent'
agent = Agent(
    name=AGENT_NAME,
    port=8001,
    mailbox=True
)

chat_proto = Protocol(spec=chat_protocol_spec)

@chat_proto.on_message(model=ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.sender = sender

    ctx.logger.info(f"[handle_chat_message] Received message from {sender}: {msg.content}")
    try:
        ack = ChatAcknowledgement(
            timestamp=datetime.now(timezone.utc),
            acknowledged_msg_id=msg.msg_id
        )
        await ctx.send(sender, ack)

        for item in msg.content:
            if isinstance(item, StartSessionContent):
                ctx.logger.info(f"Got a start session message from {sender}")
                continue
            elif isinstance(item, TextContent):
                ctx.logger.info(f"Got a message from {sender}: {item.text}")
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

### Health check related code
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


health_protocol = QuotaProtocol(
    storage_reference=agent.storage, name="HealthProtocol", version="0.1.0"
)

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

escrow_protocol = Protocol("NaraEscrowProtocol", "0.1.0")

class CoinType(Enum):
    SOLANA = "SOLANA"
    BITCOIN = "BITCOIN"
    ETHEREUM = "ETHEREUM"

class CreateListingRequest(Model):
    from_coin_type: CoinType
    to_coin_type: CoinType
    from_amount: int
    to_amount: int

class CreateListingResponse(Model):
    message: str
    request_id: str

@escrow_protocol.on_message(model=CreateListingRequest, replies={CreateListingResponse})
async def create_listing(ctx: Context, sender: str, msg: CreateListingRequest):
    ctx.logger.info(f"[create_listing] Received message from {sender}: {msg.content}")

    await ctx.send(
        sender,
        CreateListingResponse(message="Listing created successfully!", request_id="123")
    )


agent.include(escrow_protocol, publish_manifest=True)
agent.include(health_protocol, publish_manifest=True)
agent.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()