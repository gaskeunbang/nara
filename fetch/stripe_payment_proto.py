import requests
import uuid
from decimal import Decimal

from uagents import Protocol, Context

from messages import CreatePaymentMessage, CreatePaymentResponse
from config import STRIPE_API_URL, STRIPE_API_KEY, STRIPE_WEBHOOK_URL
from utils import make_canister, to_amount, to_smallest, get_price_usd, get_price_usd_number, generate_ed25519_identity, unwrap_candid, get_private_key_for_sender, get_principal_for_sender, create_checkout_session

stripe_payment_proto = Protocol(name="Stripe Payment Protocol")

@stripe_payment_proto.on_message(model=CreatePaymentMessage)
async def handle_create_payment_message(ctx: Context, sender: str, msg: CreatePaymentMessage):
    ctx.logger.info(
        f"Received Request from {sender} for Payment Link.")

    try:
        # Set sender context for utility functions
        ctx.sender = sender
        
        # Validate input parameters
        if not msg.asset or not msg.target_address:
            return CreatePaymentResponse(
                message="Asset and target address are required",
                order_id=msg.order_id,
                payment_url="",
                success=False,
            )

        coin_type = msg.asset.upper()
        token_amount = msg.amount  # Using amount field for token quantity
        
        # Validate coin type
        supported_coins = ["BTC", "ETH", "SOL", "ICP"]
        if coin_type not in supported_coins:
            return CreatePaymentResponse(
                message=f"Asset {coin_type} is not supported. Use: {', '.join(supported_coins)}",
                order_id=msg.order_id,
                payment_url="",
                success=False,
            )

        # 0) Prevent insufficient canister inventory before proceeding
        desired_e_smallest = None
        if token_amount is not None and str(token_amount) != "":
            try:
                amt_dec = Decimal(str(token_amount))
                ctx.logger.info(f"[buy_check] pre-convert: token_amount={token_amount} type={type(token_amount)} dec={amt_dec}")
                desired_e_smallest = to_smallest(coin_type, amt_dec)
                ctx.logger.info(f"[buy_check] coin={coin_type} token_amount={token_amount} desired_smallest={desired_e_smallest}")
            except Exception as ex:
                ctx.logger.info(f"[buy_check] to_smallest failed: coin={coin_type} amount={token_amount} err={ex}")
                desired_e_smallest = None

        ctx.logger.info(f"[buy_check] desired_e_smallest={desired_e_smallest}")
        ctx.logger.info(f"[buy_check] token_amount={token_amount}")
        ctx.logger.info(f"[buy_check] coin_type={coin_type}")

        if desired_e_smallest is not None and desired_e_smallest > 0:
            available_smallest = 0
            try:
                wallet_canister = make_canister("wallet", get_private_key_for_sender(ctx))
                balances_raw = wallet_canister.canister_wallet_balance()
                balances = unwrap_candid(balances_raw) or {}
                ctx.logger.info(f"[buy_check] balances={balances}")
                if coin_type == "BTC":
                    available_smallest = int(balances.get("bitcoin", 0))
                elif coin_type == "ETH":
                    # ethereum balance stored as string (wei)
                    available_smallest = int(balances.get("ethereum", "0") or 0)
                elif coin_type == "SOL":
                    available_smallest = int(balances.get("solana", 0))
                elif coin_type == "ICP":
                    available_smallest = int(balances.get("icp", 0))
                ctx.logger.info(f"[buy_check] available_smallest={available_smallest}")
            except Exception:
                # Treat unknown balance as zero to be safe
                available_smallest = 0

            if desired_e_smallest > available_smallest:
                ctx.logger.info(f"[buy_check] insufficient: desired={desired_e_smallest} available={available_smallest}")
                return CreatePaymentResponse(
                    message=(
                        "Sorry, the canister balance is not sufficient to fulfill your purchase.\n"
                        f"- Asset: {coin_type}\n"
                        f"- Requested: {token_amount} {coin_type}\n"
                        f"- Available: {to_amount(coin_type, available_smallest)} {coin_type}\n"
                        "Please reduce the amount or try another asset."
                    ),
                    order_id=msg.order_id,
                    payment_url="",
                    success=False,
                )

        # Estimate USD price for the token amount
        estimated_price_text = "Unavailable"
        amount_cents = 0
        try:
            if token_amount is not None:
                estimated_price_text = get_price_usd(coin_type, float(token_amount), logger=ctx.logger)
                # Convert USD string to cents
                usd_value = Decimal(str(estimated_price_text).replace("$", "")) if isinstance(estimated_price_text, str) else Decimal(0)
                amount_cents = int(usd_value * 100)
        except Exception as e:
            ctx.logger.error(f"Error estimating price: {e}")
            return CreatePaymentResponse(
                message=f"Error estimating price: {e}",
                order_id=msg.order_id,
                payment_url="",
                success=False,
            )

        if amount_cents <= 0:
            return CreatePaymentResponse(
                message="Invalid payment amount or price unavailable",
                order_id=msg.order_id,
                payment_url="",
                success=False,
            )

        # Create Stripe checkout session using the utility function
        try:
            session = create_checkout_session(
                order_id=str(msg.order_id),
                coin_type=coin_type.lower(),
                amount_minor=amount_cents,
                destination_address=msg.target_address,
            )
            
            if session and 'url' in session:
                return CreatePaymentResponse(
                    message="Payment link created successfully!",
                    order_id=msg.order_id,
                    payment_url=session['url'],
                    success=True,
                )
            else:
                ctx.logger.error(f"Error creating payment link: Invalid session response")
                return CreatePaymentResponse(
                    message="Unable to create payment link. Please try again later.",
                    order_id=msg.order_id,
                    payment_url="",
                    success=False,
                )
                
        except Exception as e:
            ctx.logger.error(f"Error creating Stripe checkout session: {e}")
            return CreatePaymentResponse(
                message=f"Error creating payment link: {e}",
                order_id=msg.order_id,
                payment_url="",
                success=False,
            )
      
    except Exception as e:
        ctx.logger.error(f"Error creating payment link: {e}")
        return CreatePaymentResponse(
            message=f"Error creating payment link: {e}",
            order_id=msg.order_id,
            payment_url="",
            success=False,
        )