"""
E2E tests for payment flows: create intent -> checkout -> refund.
"""
import pytest


@pytest.mark.anyio
async def test_create_payment_intent(client, mock_stripe):
    resp = await client.post("/payments/create-intent", json={
        "amount": 2000,
        "currency": "usd",
        "description": "Test payment",
        "metadata": {"order_id": "ord_001"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["payment_intent_id"] == "pi_test_123"
    assert data["client_secret"] == "pi_test_123_secret_abc"
    assert data["status"] == "requires_payment_method"

    mock_stripe.PaymentIntent.create.assert_called_once_with(
        amount=2000,
        currency="usd",
        description="Test payment",
        metadata={"order_id": "ord_001"},
        automatic_payment_methods={"enabled": True},
    )


@pytest.mark.anyio
async def test_create_checkout_session(client, mock_stripe):
    resp = await client.post("/payments/create-checkout-session", json={
        "line_items": [{"price": "price_abc", "quantity": 1}],
        "success_url": "https://example.com/success",
        "cancel_url": "https://example.com/cancel",
        "mode": "payment",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "cs_test_456"
    assert "checkout.stripe.com" in data["url"]


@pytest.mark.anyio
async def test_refund(client, mock_stripe):
    resp = await client.post("/payments/refund", json={
        "payment_intent_id": "pi_test_123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["refund_id"] == "re_test_789"
    assert data["status"] == "succeeded"


@pytest.mark.anyio
async def test_get_payment_intent(client, mock_stripe):
    resp = await client.get("/payments/intent/pi_test_123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["payment_intent_id"] == "pi_test_123"
    assert data["amount"] == 2000


@pytest.mark.anyio
async def test_full_payment_flow(client, mock_stripe):
    """E2E: create intent -> retrieve it -> refund it."""
    # Step 1: Create
    resp = await client.post("/payments/create-intent", json={
        "amount": 5000,
        "currency": "usd",
        "description": "Full flow test",
    })
    assert resp.status_code == 200
    pi_id = resp.json()["payment_intent_id"]

    # Step 2: Retrieve
    resp = await client.get(f"/payments/intent/{pi_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "requires_payment_method"

    # Step 3: Refund
    resp = await client.post("/payments/refund", json={
        "payment_intent_id": pi_id,
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "succeeded"
