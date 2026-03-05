"""
E2E tests for Stripe webhooks -> Pi dispatch pipeline.
"""
import json
import pytest


@pytest.mark.anyio
async def test_webhook_payment_succeeded_dispatches_to_pi(client, mock_pi_dispatch):
    event = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test_123",
                "amount": 2000,
                "currency": "usd",
            }
        },
    }
    resp = await client.post(
        "/webhooks/stripe",
        content=json.dumps(event),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["received"] is True
    assert data["type"] == "payment_intent.succeeded"
    assert data["pi_dispatch"]["dispatched"] is True

    mock_pi_dispatch.assert_called_once()


@pytest.mark.anyio
async def test_webhook_checkout_completed_dispatches_to_pi(client, mock_pi_dispatch):
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_456",
                "payment_status": "paid",
            }
        },
    }
    resp = await client.post(
        "/webhooks/stripe",
        content=json.dumps(event),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pi_dispatch"]["dispatched"] is True


@pytest.mark.anyio
async def test_webhook_non_routable_event_no_dispatch(client, mock_pi_dispatch):
    event = {
        "type": "customer.created",
        "data": {"object": {"id": "cus_test_999"}},
    }
    resp = await client.post(
        "/webhooks/stripe",
        content=json.dumps(event),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["received"] is True
    assert "pi_dispatch" not in data

    mock_pi_dispatch.assert_not_called()


@pytest.mark.anyio
async def test_webhook_invoice_paid(client, mock_pi_dispatch):
    event = {
        "type": "invoice.paid",
        "data": {"object": {"id": "inv_test_001", "amount_paid": 3000}},
    }
    resp = await client.post(
        "/webhooks/stripe",
        content=json.dumps(event),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["pi_dispatch"]["dispatched"] is True
