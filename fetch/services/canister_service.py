import os
import base64
import re
from dotenv import load_dotenv
from ic.canister import Canister
from ic.client import Client
from ic.identity import Identity
from ic.agent import Agent as ICAgent
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_der_private_key, Encoding, PrivateFormat, NoEncryption

load_dotenv()

BASE_URL = "http://localhost:4943" if os.getenv("DFX_NETWORK") == "local" else "https://ic0.app"

client = Client(url=BASE_URL)

def _get_candid_path(canister_name: str) -> str:
    return f"../src/declarations/{canister_name}/{canister_name}.did"


def _normalize_privkey_to_hex(priv_key: str) -> str:
    """Terima private key dalam bentuk:
    - hex (langsung)
    - PEM (berheader) PKCS8
    - base64 body dari PEM PKCS8 (tanpa header)
    dan kembalikan hex 32-byte (Ed25519 Raw).
    """
    s = (priv_key or "").strip()
    # Jika sudah hex valid
    if re.fullmatch(r"[0-9a-fA-F]+", s) and len(s) % 2 == 0:
        return s.lower()
    # Jika string mengandung header PEM
    if "-----BEGIN" in s:
        key = load_pem_private_key(s.encode("utf-8"), password=None)
        raw = key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        return raw.hex()
    # Coba asumsikan base64 body (DER PKCS8)
    try:
        der = base64.b64decode(s)
        key = load_der_private_key(der, password=None)
        raw = key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
        return raw.hex()
    except Exception:
        pass
    raise ValueError("Unsupported private key format. Provide hex, PEM, atau base64 PKCS8 body.")


def make_canister(canister_name: str, priv_key: str) -> Canister:
    try:
        priv_hex = _normalize_privkey_to_hex(priv_key)
        ic_identity = Identity(privkey=priv_hex)
        ic_agent = ICAgent(ic_identity, client)

        canister_id = os.getenv(f"CANISTER_ID_{canister_name.upper()}")
        candid = open(_get_candid_path(canister_name)).read()
        return Canister(agent=ic_agent, canister_id=canister_id, candid=candid)
    except Exception as e:
        print("Error making canister", e)
        raise e




