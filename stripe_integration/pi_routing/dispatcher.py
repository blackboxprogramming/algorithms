"""
Dispatches events and requests to Raspberry Pi endpoints.
Supports round-robin, random, and first-available routing strategies.
"""
import asyncio
import itertools
import random
import httpx
from stripe_integration.config import Config

_round_robin_cycle = None


def _get_round_robin():
    global _round_robin_cycle
    if _round_robin_cycle is None and Config.PI_ENDPOINTS:
        _round_robin_cycle = itertools.cycle(Config.PI_ENDPOINTS)
    return _round_robin_cycle


def pick_endpoint(strategy: str | None = None) -> str | None:
    endpoints = Config.PI_ENDPOINTS
    if not endpoints:
        return None

    strategy = strategy or Config.PI_ROUTING_STRATEGY

    if strategy == "random":
        return random.choice(endpoints)
    elif strategy == "first_available":
        return endpoints[0]
    else:  # round_robin
        cycle = _get_round_robin()
        return next(cycle) if cycle else None


async def dispatch_to_pi(event_type: str, event_data: dict) -> dict:
    endpoint = pick_endpoint()
    if not endpoint:
        return {"dispatched": False, "reason": "no_pi_endpoints_configured"}

    url = f"http://{endpoint}/webhook"
    payload = {"event_type": event_type, "data": event_data}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            return {
                "dispatched": True,
                "endpoint": endpoint,
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else resp.text,
            }
    except httpx.ConnectError:
        return {"dispatched": False, "endpoint": endpoint, "reason": "connection_refused"}
    except httpx.TimeoutException:
        return {"dispatched": False, "endpoint": endpoint, "reason": "timeout"}
    except Exception as e:
        return {"dispatched": False, "endpoint": endpoint, "reason": str(e)}


async def forward_request(path: str, method: str = "GET", body: dict | None = None,
                          strategy: str | None = None) -> dict:
    endpoint = pick_endpoint(strategy)
    if not endpoint:
        return {"forwarded": False, "reason": "no_pi_endpoints_configured"}

    url = f"http://{endpoint}{path}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if method.upper() == "POST":
                resp = await client.post(url, json=body or {})
            elif method.upper() == "PUT":
                resp = await client.put(url, json=body or {})
            elif method.upper() == "DELETE":
                resp = await client.delete(url)
            else:
                resp = await client.get(url)

            return {
                "forwarded": True,
                "endpoint": endpoint,
                "status_code": resp.status_code,
                "response": resp.text,
            }
    except Exception as e:
        return {"forwarded": False, "endpoint": endpoint, "reason": str(e)}
