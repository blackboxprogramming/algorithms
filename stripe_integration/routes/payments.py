"""
Stripe payment endpoints — create intents, checkout sessions, refunds.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import stripe
from stripe_integration.config import Config

router = APIRouter()
stripe.api_key = Config.STRIPE_SECRET_KEY


class CreatePaymentRequest(BaseModel):
    amount: int  # in cents
    currency: str = "usd"
    description: str = ""
    metadata: dict = {}


class CreateCheckoutRequest(BaseModel):
    line_items: list  # [{"price": "price_xxx", "quantity": 1}]
    success_url: str
    cancel_url: str
    mode: str = "payment"  # "payment", "subscription", "setup"


class RefundRequest(BaseModel):
    payment_intent_id: str
    amount: int | None = None  # None = full refund


@router.post("/create-intent")
async def create_payment_intent(req: CreatePaymentRequest):
    try:
        intent = stripe.PaymentIntent.create(
            amount=req.amount,
            currency=req.currency,
            description=req.description,
            metadata=req.metadata,
            automatic_payment_methods={"enabled": True},
        )
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "status": intent.status,
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/create-checkout-session")
async def create_checkout_session(req: CreateCheckoutRequest):
    try:
        session = stripe.checkout.Session.create(
            line_items=req.line_items,
            mode=req.mode,
            success_url=req.success_url,
            cancel_url=req.cancel_url,
        )
        return {"session_id": session.id, "url": session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refund")
async def create_refund(req: RefundRequest):
    try:
        params = {"payment_intent": req.payment_intent_id}
        if req.amount is not None:
            params["amount"] = req.amount
        refund = stripe.Refund.create(**params)
        return {"refund_id": refund.id, "status": refund.status}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/intent/{payment_intent_id}")
async def get_payment_intent(payment_intent_id: str):
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return {
            "payment_intent_id": intent.id,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status,
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
