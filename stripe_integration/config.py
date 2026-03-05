"""
Configuration for Stripe integration and Pi routing.
All secrets come from environment variables — nothing hardcoded.
"""
import os


class Config:
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    # Raspberry Pi endpoints — comma-separated list of host:port
    # e.g. "192.168.1.100:8000,192.168.1.101:8000"
    PI_ENDPOINTS = [
        ep.strip()
        for ep in os.environ.get("PI_ENDPOINTS", "").split(",")
        if ep.strip()
    ]

    # Routing strategy: "round_robin", "random", "first_available"
    PI_ROUTING_STRATEGY = os.environ.get("PI_ROUTING_STRATEGY", "round_robin")

    HOST = os.environ.get("SERVICE_HOST", "0.0.0.0")
    PORT = int(os.environ.get("SERVICE_PORT", "8080"))
