"""
Main FastAPI application — Stripe payments + Pi routing.
"""
from fastapi import FastAPI
from stripe_integration.routes.payments import router as payments_router
from stripe_integration.routes.webhooks import router as webhooks_router
from stripe_integration.pi_routing.router import router as pi_router

app = FastAPI(title="Stripe + Pi Integration", version="1.0.0")

app.include_router(payments_router, prefix="/payments", tags=["payments"])
app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
app.include_router(pi_router, prefix="/pi", tags=["pi-routing"])


@app.get("/health")
async def health():
    return {"status": "ok"}
