"""
Shared fixtures for e2e tests.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

# Set env vars before importing app
os.environ["STRIPE_SECRET_KEY"] = "sk_test_fake_key_for_testing"
os.environ["STRIPE_WEBHOOK_SECRET"] = ""
os.environ["PI_ENDPOINTS"] = "127.0.0.1:9100,127.0.0.1:9101"
os.environ["PI_ROUTING_STRATEGY"] = "round_robin"

from stripe_integration.app import app  # noqa: E402


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def mock_stripe():
    """Patches stripe API calls with realistic fake responses."""
    with patch("stripe_integration.routes.payments.stripe") as mock:
        # PaymentIntent.create
        intent = MagicMock()
        intent.id = "pi_test_123"
        intent.client_secret = "pi_test_123_secret_abc"
        intent.status = "requires_payment_method"
        intent.amount = 2000
        intent.currency = "usd"
        mock.PaymentIntent.create.return_value = intent
        mock.PaymentIntent.retrieve.return_value = intent

        # Checkout Session
        session = MagicMock()
        session.id = "cs_test_456"
        session.url = "https://checkout.stripe.com/pay/cs_test_456"
        mock.checkout.Session.create.return_value = session

        # Refund
        refund = MagicMock()
        refund.id = "re_test_789"
        refund.status = "succeeded"
        mock.Refund.create.return_value = refund

        # Error class for exception handling
        mock.error.StripeError = Exception

        yield mock


@pytest.fixture
def mock_pi_dispatch():
    """Patches Pi dispatcher to avoid real network calls."""
    with patch("stripe_integration.routes.webhooks.dispatch_to_pi") as mock:
        async def fake_dispatch(event_type, event_data):
            return {
                "dispatched": True,
                "endpoint": "127.0.0.1:9100",
                "status_code": 200,
                "response": {"processed": True},
            }
        mock.side_effect = fake_dispatch
        yield mock
