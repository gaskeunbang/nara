import base64, hashlib, struct, zlib, os
from cryptography.hazmat.primitives.asymmetric import ed25519, ec
from cryptography.hazmat.primitives import serialization

def to_der_spki(pubkey):
    # Sudah berbentuk SubjectPublicKeyInfo (DER) sesuai RFC untuk masing-masing kurva
    return pubkey.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

def principal_from_der_pubkey(der_pubkey: bytes) -> bytes:
    digest = hashlib.sha224(der_pubkey).digest()          # 28 bytes
    return b"\x02" + digest                               # 1 + 28 = 29 bytes

def text_encode_principal(principal_bytes: bytes) -> str:
    crc = zlib.crc32(principal_bytes) & 0xFFFFFFFF
    data = struct.pack("<I", crc) + principal_bytes       # prepend CRC32 (little-endian)
    b32 = base64.b32encode(data).decode("ascii").lower().strip("=")
    # tambahkan '-' tiap 5 karakter biar seperti "w7x7r-cok77-xa..."
    return "-".join(b32[i:i+5] for i in range(0, len(b32), 5))

def save_keypair_ed25519(priv, path_prefix="ed25519"):
    # Simpan private key (PEM, encrypted optional)
    pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(f"{path_prefix}_private.pem", "wb") as f:
        f.write(pem)
    # Simpan public key (PEM)
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    with open(f"{path_prefix}_public.pem", "wb") as f:
        f.write(pub_pem)

def pem_to_base64_text(pem_str: str) -> str:
    """Ambil isi base64 dari string PEM dan return sebagai satu baris tanpa header/footer."""
    lines = pem_str.strip().splitlines()
    inner = [ln for ln in lines if not ln.startswith("-----")]
    return "".join(inner).strip()

def generate_ed25519_principal():
    # 1) generate keypair
    sk = ed25519.Ed25519PrivateKey.generate()
    pk = sk.public_key()
    # 2) DER SPKI public key
    der = to_der_spki(pk)
    # 3) principal bytes
    principal = principal_from_der_pubkey(der)
    # 4) textual principal
    principal_text = text_encode_principal(principal)
    # 5) serialize keys ke string (PEM), JANGAN simpan ke file
    priv_pem = sk.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    pub_pem = pk.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    # 6) ambil hanya teks base64 di dalam PEM
    pub_txt = pem_to_base64_text(pub_pem)
    priv_txt = pem_to_base64_text(priv_pem)
    # return hanya principal_text, pub_key (string), priv_key (string)
    return principal_text, pub_txt, priv_txt
