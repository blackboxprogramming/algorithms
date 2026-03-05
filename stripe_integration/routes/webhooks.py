"""
Stripe webhook handler — verifies signatures, dispatches events.
"""
from fastapi import APIRouter, Request, HTTPException
import stripe
from stripe_integration.config import Config
from stripe_integration.pi_routing.dispatcher import dispatch_to_pi

router = APIRouter()
stripe.api_key = Config.STRIPE_SECRET_KEY


@router.post("/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if Config.STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type", "") if isinstance(event, dict) else event.type
    event_data = event.get("data", {}) if isinstance(event, dict) else event.data

    # Route payment events to Pis for processing/fulfillment
    routable_events = {
        "payment_intent.succeeded",
        "checkout.session.completed",
        "invoice.paid",
        "charge.succeeded",
    }

    result = {"received": True, "type": event_type}

    if event_type in routable_events:
        pi_result = await dispatch_to_pi(event_type, event_data)
        result["pi_dispatch"] = pi_result

    return result
