from fastapi import FastAPI

from src.fast_decorators.rate_limiter import rate_limiter


app = FastAPI()


@app.get("/limited_small")
@rate_limiter(max_requests=3, time_delta=5)
async def limited_endpoint_small():
    return {"ok": True}


@app.get("/limited_big")
@rate_limiter(max_requests=10, time_delta=5)
async def limited_endpoint_big():
    return {"ok": True}
