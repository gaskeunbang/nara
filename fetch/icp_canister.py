from pathlib import Path
import os

from ic.canister import Canister
from ic.client import Client
from ic.identity import Identity
from ic.agent import Agent as ICAgent


def load_env_from_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def init_backend() -> Canister:
    project_root_dir = Path(__file__).resolve().parents[1]
    env_file_path = project_root_dir / ".env"
    load_env_from_file(env_file_path)

    canister_id_env = os.getenv("CANISTER_ID_ESCROW")
    if not canister_id_env:
        raise EnvironmentError(
            "Environment variable CANISTER_ID or CANISTER_ID_ESCROW must be set"
        )
    canister_id = canister_id_env

    dfx_network = os.getenv("DFX_NETWORK")
    if not dfx_network:
        raise EnvironmentError("Environment variable DFX_NETWORK must be set (ic|local)")

    dfx_network = dfx_network.lower()
    if dfx_network == "ic":
        base_url = "https://icp0.io"
    elif dfx_network == "local":
        base_url = "http://127.0.0.1:4943"
    else:
        raise ValueError(f"DFX_NETWORK must be 'ic' or 'local', got: {dfx_network}")

    candid_env_path = os.getenv("CANISTER_CANDID_PATH_ESCROW")
    if not candid_env_path:
        raise EnvironmentError(
            "Environment variable CANISTER_CANDID_PATH_ESCROW must be set to the .did file path"
        )

    candid_path = Path(candid_env_path)
    if not candid_path.exists():
        raise FileNotFoundError(
            f"CANISTER_CANDID_PATH_ESCROW points to a non-existent file: {candid_env_path}"
        )

    canister_did = candid_path.read_text()

    identity = Identity()
    client = Client(url=base_url)
    agent = ICAgent(identity, client)
    return Canister(agent=agent, canister_id=canister_id, candid=canister_did)


# Eagerly initialize a shared backend canister instance
backend: Canister = init_backend()

