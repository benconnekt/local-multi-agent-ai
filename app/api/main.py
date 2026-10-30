
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agents import router as agents_router
from app.api.routes.health import router as health_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.trading import router as trading_router
from app.api.routes.trading_datasets import router as trading_datasets_router
from app.api.routes.trading_strategy import router as trading_strategy_router

app = FastAPI(
    title="Local Agent Studio API",
    version="0.1.0",
    description="Local multi-agent engineering platform API",
)

app.add_middleware(
    CORSMiddleware,
    # allow_origins=[
    #     "http://localhost:3000",
    #     "http://127.0.0.1:3000",
    # ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):[0-9]{1,5}$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(agents_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(trading_router   , prefix="/api/v1")
app.include_router(trading_datasets_router, prefix="/api/v1")
app.include_router(trading_strategy_router, prefix="/api/v1")
