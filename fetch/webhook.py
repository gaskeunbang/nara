import os
import json
from flask import Flask, request, jsonify
import time

from utils.stripe import verify_webhook_signature, extract_checkout_metadata
from utils.canister import make_canister
from utils.candid import unwrap_candid
from utils.coin import to_smallest
from utils.pricing import get_price_usd_number
from config.settings import STRIPE_API_KEY


app = Flask(__name__)


def _load_controller_private_key() -> str:
    """Load controller private key from principal/private.pem file.

    Priority:
    1) principal/private.pem (alongside project root)
    2) fetch/principal/private.pem (if present)
    3) CONTROLLER_PRIVATE_KEY env (fallback; hex/PEM allowed)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))  # .../fetch
    candidates = [
        os.path.abspath(os.path.join(base_dir, "..", "principal", "private.pem")),
        os.path.abspath(os.path.join(base_dir, "principal", "private.pem")),
    ]
    for path in candidates:
        try:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    pem = f.read().strip()
                    if pem:
                        print(f"[Webhook] Using controller key from {path}")
                        return pem
        except Exception:
            pass

    env_key = os.getenv("CONTROLLER_PRIVATE_KEY", "").strip()
    if env_key:
        print("[Webhook] Using controller key from CONTROLLER_PRIVATE_KEY env (fallback)")
        return env_key

    raise RuntimeError(
        "Controller private key not found. Place your PEM at principal/private.pem or set CONTROLLER_PRIVATE_KEY."
    )

@app.route("/health", methods=["GET"])
def health() -> tuple:
    return jsonify({"status": "ok"}), 200


@app.route("/order/success", methods=["GET"])
def order_success() -> tuple:
    session_id = request.args.get("session_id")
    return jsonify({
        "status": "ok",
        "message": "Payment completed. Your order is being processed.",
        "session_id": session_id,
        "note": "Token will be sent after we receive payment confirmation."
    }), 200


@app.route("/cancel", methods=["GET"])
def order_cancel() -> tuple:
    return jsonify({
        "status": "cancelled",
        "message": "Payment was cancelled. No charges were made."
    }), 200


@app.route("/stripe/webhook", methods=["POST"])
def stripe_webhook() -> tuple:

    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    sig_header = request.headers.get("Stripe-Signature", "")
    payload = request.get_data()
    print(f"[Stripe] Payload: {payload}")
    print(f"[Stripe] secret: {secret}")
    print(f"[Stripe] sig_header: {sig_header}")

    # Verify signature (skip if no secret configured)
    if secret and not verify_webhook_signature(payload, sig_header, secret):
        return jsonify({"error": "invalid signature"}), 400

    event = request.get_json(force=True, silent=True) or {}
    event_type = event.get("type")

    if event_type == "checkout.session.completed":
        metadata = extract_checkout_metadata(event)
        coin_type = (metadata.get("coin_type") or "").lower()
        destination = metadata.get("destination_address") or ""

        if not coin_type or not destination:
            return jsonify({"status": "ignored", "reason": "missing metadata"}), 200

        # Enforce 5-minute validity window based on session creation time
        obj = event.get("data", {}).get("object", {})
        created_ts = obj.get("created")  # seconds since epoch
        try:
            created_ts = int(created_ts) if created_ts is not None else None
        except Exception:
            created_ts = None
        now = int(time.time())
        if created_ts is not None and (now - created_ts) > 300:
            return jsonify({"status": "expired", "message": "Payment link expired (over 5 minutes)."}), 200

        # Determine token amount based on paid USD amount
        amount_minor_str = metadata.get("amount_minor") or "0"
        try:
            usd_cents = int(amount_minor_str)
        except Exception:
            usd_cents = 0
        usd_amount = usd_cents / 100.0
        price_usd = get_price_usd_number(coin_type)
        if not price_usd or price_usd <= 0:
            return jsonify({"status": "error", "message": "Unable to fetch token price"}), 500
        # token_amount = USD / price_per_token
        from decimal import Decimal
        token_amount = Decimal(str(usd_amount)) / price_usd
        # Convert to smallest unit for blockchain send
        smallest = to_smallest(coin_type.upper(), token_amount)

        try:
            controller_priv = _load_controller_private_key()
            wallet = make_canister("wallet", controller_priv)
            # For demo: send a fixed nominal amount after successful payment
            if coin_type in {"btc", "eth", "sol"}:
                # Use canister_send_token for chain tokens
                res_raw = wallet.canister_send_token(destination, smallest, coin_type)
                res = unwrap_candid(res_raw)
            elif coin_type == "icp":
                # ICP transfer via canister_send_token (amount in e8s)
                res_raw = wallet.canister_send_token(destination, smallest, "icp")
                res = unwrap_candid(res_raw)
            else:
                return jsonify({"status": "ignored", "reason": "unsupported coin"}), 200

            return jsonify({"status": "ok", "tx": res}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # Acknowledge other events
    return jsonify({"status": "ignored"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("WEBHOOK_PORT", 8080)))


