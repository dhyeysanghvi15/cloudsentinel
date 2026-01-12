from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings

from .routers.scan import router as scan_router
from .routers.policy import router as policy_router
from .routers.sim import router as sim_router

settings = get_settings()
app = FastAPI(title="cloudsentinel api", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}


app.include_router(scan_router)
app.include_router(policy_router)
app.include_router(sim_router)
