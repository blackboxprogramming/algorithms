"""
Unit tests for the Pi dispatcher logic — routing strategies and dispatch behavior.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


def test_pick_endpoint_round_robin():
    with patch("stripe_integration.pi_routing.dispatcher.Config") as MockConfig:
        MockConfig.PI_ENDPOINTS = ["pi1:8000", "pi2:8000", "pi3:8000"]
        MockConfig.PI_ROUTING_STRATEGY = "round_robin"

        # Reset the cycle
        import stripe_integration.pi_routing.dispatcher as dispatcher
        dispatcher._round_robin_cycle = None

        results = [dispatcher.pick_endpoint() for _ in range(6)]
        assert results == [
            "pi1:8000", "pi2:8000", "pi3:8000",
            "pi1:8000", "pi2:8000", "pi3:8000",
        ]


def test_pick_endpoint_random():
    with patch("stripe_integration.pi_routing.dispatcher.Config") as MockConfig:
        MockConfig.PI_ENDPOINTS = ["pi1:8000", "pi2:8000"]
        MockConfig.PI_ROUTING_STRATEGY = "random"

        import stripe_integration.pi_routing.dispatcher as dispatcher
        result = dispatcher.pick_endpoint("random")
        assert result in ["pi1:8000", "pi2:8000"]


def test_pick_endpoint_first_available():
    with patch("stripe_integration.pi_routing.dispatcher.Config") as MockConfig:
        MockConfig.PI_ENDPOINTS = ["pi1:8000", "pi2:8000"]

        import stripe_integration.pi_routing.dispatcher as dispatcher
        result = dispatcher.pick_endpoint("first_available")
        assert result == "pi1:8000"


def test_pick_endpoint_no_endpoints():
    with patch("stripe_integration.pi_routing.dispatcher.Config") as MockConfig:
        MockConfig.PI_ENDPOINTS = []

        import stripe_integration.pi_routing.dispatcher as dispatcher
        result = dispatcher.pick_endpoint()
        assert result is None


@pytest.mark.anyio
async def test_dispatch_to_pi_no_endpoints():
    with patch("stripe_integration.pi_routing.dispatcher.Config") as MockConfig:
        MockConfig.PI_ENDPOINTS = []

        from stripe_integration.pi_routing.dispatcher import dispatch_to_pi
        result = await dispatch_to_pi("payment_intent.succeeded", {})
        assert result["dispatched"] is False
        assert result["reason"] == "no_pi_endpoints_configured"


@pytest.mark.anyio
async def test_dispatch_to_pi_connection_error():
    with patch("stripe_integration.pi_routing.dispatcher.pick_endpoint", return_value="192.168.1.99:8000"):
        with patch("stripe_integration.pi_routing.dispatcher.httpx.AsyncClient") as MockClient:
            import httpx
            mock_instance = AsyncMock()
            mock_instance.post.side_effect = httpx.ConnectError("Connection refused")
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_instance

            from stripe_integration.pi_routing.dispatcher import dispatch_to_pi
            result = await dispatch_to_pi("payment_intent.succeeded", {"id": "pi_123"})
            assert result["dispatched"] is False
            assert result["reason"] == "connection_refused"
