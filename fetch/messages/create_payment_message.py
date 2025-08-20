from uagents import Model

class CreatePaymentMessage(Model):
    order_id: float
    asset: str
    customer_id: str
    target_address: str
    principal: str

class CreatePaymentResponse(Model):
    message: str
    success: bool
    order_id: float
    payment_url: str