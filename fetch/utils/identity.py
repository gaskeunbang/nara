import base64, hashlib, struct, zlib
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# --- utils ---

def to_der_spki(pubkey):
    return pubkey.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

def principal_from_der_pubkey(der_pubkey: bytes) -> bytes:
    # self-authenticating: 0x02 || sha224(der_pubkey)
    digest = hashlib.sha224(der_pubkey).digest()  # 28 bytes
    return b"\x02" + digest                       # 29 bytes

def text_encode_principal(principal_bytes: bytes) -> str:
    # CRC32 MUST be big-endian per IC spec
    crc = zlib.crc32(principal_bytes) & 0xFFFFFFFF
    data = struct.pack(">I", crc) + principal_bytes  # <-- big-endian
    b32 = base64.b32encode(data).decode("ascii").lower().rstrip("=")
    return "-".join(b32[i:i+5] for i in range(0, len(b32), 5))

def text_decode_principal(text: str) -> bytes:
    # optional validator: decode & verify checksum
    raw = text.replace("-", "").upper()
    pad = "=" * (-len(raw) % 8)
    data = base64.b32decode(raw + pad)
    crc_be = data[:4]
    body = data[4:]
    calc = struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    if crc_be != calc:
        raise ValueError("Invalid principal checksum")
    return body

def pem_to_base64_text(pem_str: str) -> str:
    lines = pem_str.strip().splitlines()
    inner = [ln for ln in lines if not ln.startswith("-----")]
    return "".join(inner).strip()

# --- main API ---

def generate_ed25519_principal():
    # 1) keypair
    sk = ed25519.Ed25519PrivateKey.generate()
    pk = sk.public_key()
    # 2) DER SPKI public key
    der = to_der_spki(pk)
    # 3) principal bytes
    principal = principal_from_der_pubkey(der)
    # 4) textual principal (with correct big-endian CRC32)
    principal_text = text_encode_principal(principal)
    # 5) serialize keys (PEM strings)
    priv_pem = sk.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    pub_pem = pk.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    # 6) hanya isi base64-nya (opsional)
    pub_txt = pem_to_base64_text(pub_pem)
    priv_txt = pem_to_base64_text(priv_pem)
    return principal_text, pub_txt, priv_txt

# --- quick self-test ---
if __name__ == "__main__":
    ptxt, pub, priv, pbytes = generate_ed25519_principal()
    assert text_decode_principal(ptxt) == pbytes  # checksum ok
    print("principal:", ptxt)
