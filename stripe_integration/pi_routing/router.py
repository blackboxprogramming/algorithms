"""
API routes for Pi management and request forwarding.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from stripe_integration.config import Config
from stripe_integration.pi_routing.dispatcher import forward_request, pick_endpoint

router = APIRouter()


class ForwardRequest(BaseModel):
    path: str
    method: str = "GET"
    body: dict | None = None
    strategy: str | None = None


@router.get("/endpoints")
async def list_endpoints():
    return {
        "endpoints": Config.PI_ENDPOINTS,
        "strategy": Config.PI_ROUTING_STRATEGY,
        "count": len(Config.PI_ENDPOINTS),
    }


@router.post("/forward")
async def forward_to_pi(req: ForwardRequest):
    result = await forward_request(
        path=req.path,
        method=req.method,
        body=req.body,
        strategy=req.strategy,
    )
    if not result.get("forwarded"):
        raise HTTPException(status_code=502, detail=result)
    return result


@router.get("/health")
async def pi_health_check():
    """Check connectivity to all configured Pis."""
    results = {}
    for endpoint in Config.PI_ENDPOINTS:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"http://{endpoint}/health")
                results[endpoint] = {
                    "status": "up",
                    "status_code": resp.status_code,
                }
        except Exception as e:
            results[endpoint] = {"status": "down", "error": str(e)}

    up_count = sum(1 for r in results.values() if r["status"] == "up")
    return {
        "total": len(Config.PI_ENDPOINTS),
        "up": up_count,
        "down": len(Config.PI_ENDPOINTS) - up_count,
        "endpoints": results,
    }
