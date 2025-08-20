import requests
import uuid

from uagents import Protocol, Context

from messages.create_payment_message import CreatePaymentMessage, CreatePaymentResponse
from config.settings import STRIPE_API_URL, STRIPE_API_KEY, STRIPE_WEBHOOK_URL

stripe_payment_proto = Protocol(name="Stripe Payment Protocol")

@stripe_payment_proto.on_message(model=CreatePaymentMessage)
async def handle_create_payment_message(ctx: Context, sender: str, msg: CreatePaymentMessage):
    ctx.logger.info(
        f"Received Request from {sender} for Payment Link.")

    try:
      payload = {
        'customer_creation': 'always',
        'mode': 'payment',
        'payment_intent_data[metadata][order_id]': msg.order_id,
        'success_url': f"{STRIPE_WEBHOOK_URL}/order/success?session_id={{CHECKOUT_SESSION_ID}}",
        'cancel_url': f"{STRIPE_WEBHOOK_URL}/cancel"
      }
      
      # Add items
      payload[f'line_items[0][price_data][currency]'] = msg.asset
      payload[f'line_items[0][price_data][product_data][name]'] = msg.asset
      payload[f'line_items[0][price_data][unit_amount]'] = msg.amount
      payload[f'line_items[0][quantity]'] = 1

      headers = {
          'Authorization': f'Bearer {STRIPE_API_KEY}',
          'Content-Type': 'application/x-www-form-urlencoded'
      }

      response = requests.post(f"{STRIPE_API_URL}/checkout/sessions", headers=headers, data=payload)
      session = response.json()
      order_id = str(uuid.uuid4())

      if response.status_code == 200 and 'url' in session:
        resp = await ctx.send(
          sender,
          CreatePaymentResponse(
            message="Payment link generated successfully!",
            order_id=order_id,
            payment_url=session['url'],
            success=True,
          ),
        )
      else:
        ctx.logger.error(f"Error creating payment link: {response.text}")
        return CreatePaymentResponse(
          message="Can't generate payment link, please try again after some time.!",
          order_id=order_id,
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