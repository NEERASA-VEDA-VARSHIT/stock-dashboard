import os
from pathlib import Path


def _load_env_file(env_path: Path) -> None:
	# Fallback parser so .env works even when python-dotenv is not installed.
	if not env_path.exists():
		return

	for raw_line in env_path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		os.environ.setdefault(key, value)


# Load .env file (prefer python-dotenv if available)
env_path = Path(__file__).parent.parent.parent / ".env"
try:
	from dotenv import load_dotenv  # type: ignore

	load_dotenv(dotenv_path=env_path)
except Exception:
	_load_env_file(env_path)

# =============================================================================
# APP CONFIGURATION
# =============================================================================
APP_NAME = os.getenv("APP_NAME", "Stock Dashboard")
API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DATABASE_URL = (os.getenv("DATABASE_URL") or "sqlite:///./stock_data.db").strip()

# =============================================================================
# AI / GEMINI CONFIGURATION
# =============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# =============================================================================
# STOCK PROVIDER CONFIGURATION
# =============================================================================
STOCK_PROVIDER_PRIMARY = os.getenv("STOCK_PROVIDER_PRIMARY", "yahoo")
STOCK_PROVIDER_FALLBACK = os.getenv("STOCK_PROVIDER_FALLBACK", "alpha_vantage")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# =============================================================================
# SEARCH / SYMBOLS CONFIGURATION
# =============================================================================
SYMBOLS_DATASET_PATH = os.getenv("SYMBOLS_DATASET_PATH", str(Path(__file__).parent.parent / "data" / "symbols.csv"))
ENABLE_YAHOO_SEARCH_FALLBACK = os.getenv("ENABLE_YAHOO_SEARCH_FALLBACK", "true").lower() in ("true", "1", "yes")

# =============================================================================
# INGESTION / SECURITY CONFIGURATION
# =============================================================================
INGEST_ADMIN_KEY = os.getenv("INGEST_ADMIN_KEY", "")
REQUIRE_INGEST_ADMIN = os.getenv("REQUIRE_INGEST_ADMIN", "true").lower() in ("true", "1", "yes")
