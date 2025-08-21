## Stripe Payment Protocol - Update Notes

### Overview

The `stripe_payment_proto.py` file has been updated to integrate the buy-crypto logic consistent with `chat_proto.py`. This protocol is a standalone `StripePaymentProtocol`, separate from the chat protocol.

### Key Changes

#### 1) Message Model Update

Updates in `fetch/messages/create_payment_message.py`:

- `order_id`: now `str` (was `float`)
- `amount`: new `float` field for the token amount to purchase
- Other fields remain the same

#### 2) Protocol Logic Update

Enhancements in `fetch/protocols/stripe_payment_proto.py`:

- Input validation (supported assets: BTC, ETH, SOL, ICP; target address; amount)
- Canister balance check to prevent overselling
- USD price estimation using `get_price_usd()` and conversion to cents
- Stripe Checkout creation via `create_checkout_session()` with complete metadata
- Robust error handling and logging

#### 3) Dependencies

This protocol reuses utilities from the chat flow:

- `utils.canister.make_canister()`
- `utils.coin.to_amount()`, `to_smallest()`
- `utils.pricing.get_price_usd()`
- `utils.stripe.create_checkout_session()`
- `utils.context.get_private_key_for_sender()`
- `utils.candid.unwrap_candid()`

### How to Use

1. Send a `CreatePaymentMessage`:

```python
from messages.create_payment_message import CreatePaymentMessage

message = CreatePaymentMessage(
    order_id="order_123",
    asset="BTC",
    amount=0.001,  # 0.001 BTC
    customer_id="customer_456",
    target_address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    principal="principal_789"
)
```

2. The protocol will:

1) Validate inputs
2) Check canister balance
3) Estimate USD price
4) Create a Stripe Checkout Session
5) Return a `CreatePaymentResponse`

3. Response Format

```python
CreatePaymentResponse(
    message="Payment link created successfully!",
    success=True,
    order_id="order_123",
    payment_url="https://checkout.stripe.com/pay/..."
)
```

### Error Handling Examples

Insufficient Balance

```
"Sorry, the canister balance is not sufficient to fulfill your purchase.
- Asset: BTC
- Requested: 0.001 BTC
- Available: 0.0005 BTC
Please reduce the amount or try another asset."
```

Invalid Asset

```
"Asset DOGE is not supported. Use: BTC, ETH, SOL, ICP"
```

Price Estimation Error

```
"Error estimating price: [error details]"
```

### Environment Variables

Make sure the following environment variables are set:

- `STRIPE_API_KEY`
- `STRIPE_API_URL`
- `STRIPE_WEBHOOK_URL`
- `CANISTER_ID_WALLET`
- `CANISTER_ID_ICP_LEDGER`

### Differences from Chat Protocol

- Separate protocol type (`StripePaymentProtocol`)
- Direct payment processing without the confirmation flow
- Response returns a payment link immediately
- Best used for automated payment processing

### Security Considerations

- Balance validation prevents overselling
- Input validation sanitizes user inputs
- Error handling avoids leaking sensitive info
- Extensive logging for debugging
