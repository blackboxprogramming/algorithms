"""
E2E tests for Pi routing — endpoint listing, forwarding, health checks.
"""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.anyio
async def test_list_pi_endpoints(client):
    resp = await client.get("/pi/endpoints")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert "127.0.0.1:9100" in data["endpoints"]
    assert data["strategy"] == "round_robin"


@pytest.mark.anyio
async def test_forward_to_pi_success(client):
    with patch("stripe_integration.pi_routing.router.forward_request") as mock_fwd:
        async def fake_forward(**kwargs):
            return {
                "forwarded": True,
                "endpoint": "127.0.0.1:9100",
                "status_code": 200,
                "response": '{"ok": true}',
            }
        mock_fwd.side_effect = fake_forward

        resp = await client.post("/pi/forward", json={
            "path": "/api/data",
            "method": "GET",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["forwarded"] is True
        assert data["endpoint"] == "127.0.0.1:9100"


@pytest.mark.anyio
async def test_forward_to_pi_no_endpoints(client):
    with patch("stripe_integration.pi_routing.router.forward_request") as mock_fwd:
        async def fake_forward(**kwargs):
            return {"forwarded": False, "reason": "no_pi_endpoints_configured"}
        mock_fwd.side_effect = fake_forward

        resp = await client.post("/pi/forward", json={
            "path": "/api/data",
            "method": "GET",
        })
        assert resp.status_code == 502


@pytest.mark.anyio
async def test_pi_health_check(client):
    """Mock httpx to simulate Pi health responses."""
    import httpx

    mock_response = AsyncMock()
    mock_response.status_code = 200

    with patch("stripe_integration.pi_routing.router.httpx.AsyncClient") as MockClient:
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        MockClient.return_value = mock_client_instance

        resp = await client.get("/pi/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["up"] == 2


@pytest.mark.anyio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
