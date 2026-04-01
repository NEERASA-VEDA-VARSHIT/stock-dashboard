from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.stock_routes import router as stock_router
from app.core.config import API_V1_PREFIX, APP_NAME, CORS_ORIGINS
from app.core.schema_sync import init_db_schema
from app.models.stock import StockFeature, StockPrice  # noqa: F401

app = FastAPI(title=APP_NAME, version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=CORS_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
	init_db_schema()


@app.get("/health")
def health_check() -> dict:
	return {"status": "ok"}

app.include_router(stock_router, prefix=API_V1_PREFIX)