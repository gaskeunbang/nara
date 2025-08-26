from uagents import Agent

# Protocols
from protocols.health_proto import create_health_protocol
from protocols.chat_proto import chat_proto
from protocols.stripe_payment_proto import stripe_payment_proto
# Settings
from config.settings import ASI1_BASE_URL, ASI1_HEADERS

# Setup agent
AGENT_NAME = 'Nara Wallet Agent'
location = {"latitude": -6.9175, "longitude": 107.6191}
agent = Agent(
    name=AGENT_NAME,
    seed="nara-wallet-agent",
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)
agent.location = {"latitude": -6.9175, "longitude": 107.6191}

# Attach protocols to agent
health_protocol = create_health_protocol(agent, AGENT_NAME)
agent.include(health_protocol, publish_manifest=True)
agent.include(chat_proto, publish_manifest=True)
agent.include(stripe_payment_proto, publish_manifest=True)

if __name__ == "__main__":
    agent.run()