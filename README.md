# Stock Dashboard

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-0.135-009688?logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6?logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-336791?logo=postgresql)
![License](https://img.shields.io/badge/License-MIT-blue)
![Build](https://img.shields.io/badge/Build-passing-brightgreen)

</div>

## Project Overview

Stock Dashboard is a modern full-stack application for real-time stock market data analysis and visualization. It fetches live stock data from multiple providers (Yahoo Finance, AlphaVantage), performs data transformation and feature engineering, and presents insights through an intuitive web interface. Built with FastAPI, SQLAlchemy, Next.js, and TypeScript, the application follows clean architecture principles with strict separation of concerns and production-grade DB integrity constraints.

**Key Features:**
- 📊 Real-time stock data fetching with provider fallback
- 🔄 Automated data pipeline (ETL) with transformation and cleaning
- 📈 Interactive comparison charts with normalized performance metrics
- 🏢 Structured data storage with raw/derived separation
- 🔐 Type-safe API contracts between backend and frontend
- ⚡ Efficient prefix-scoped caching system
- 🎯 Modular service architecture (market data, signals, predictions, AI)

## Project Structure

```
├── app/                                 # FastAPI Backend
│   ├── main.py                          # Application entry point
│   ├── __pycache__/
│   ├── api/
│   │   └── v1/
│   │       ├── stock_routes.py          # Stock API endpoints
│   │       └── __pycache__/
│   ├── core/
│   │   ├── config.py                    # Configuration management
│   │   ├── db.py                        # Database setup & session
│   │   ├── schema_sync.py               # DB schema initialization & migrations
│   │   └── __pycache__/
│   ├── models/
│   │   ├── stock.py                     # SQLAlchemy ORM models
│   │   │   ├── StockPrice               # Raw OHLCV (immutable)
│   │   │   └── StockFeature             # Derived metrics
│   │   └── __pycache__/
│   ├── pipelines/
│   │   ├── cleaner.py                   # Data validation & cleaning
│   │   ├── fetcher.py                   # Multi-provider data fetching
│   │   ├── loader.py                    # ETL write to split tables
│   │   └── transformer.py               # Feature engineering & transformations
│   ├── repositories/
│   │   └── stock_repository.py          # Data access layer with explicit joins
│   ├── schemas/
│   │   └── stock_schema.py              # Pydantic response schemas
│   ├── services/
│   │   ├── market_data_service.py       # Market data orchestration
│   │   ├── signal_service.py            # Trading signals generation
│   │   ├── prediction_service.py        # Price predictions
│   │   ├── ai_service.py                # AI-powered insights
│   │   ├── stock_service.py             # Service orchestration layer
│   │   └── __pycache__/
│   └── utils/
│       └── cache.py                     # TTL cache with prefix invalidation
│
├── scripts/
│   └── run_pipeline.py                  # Standalone pipeline execution
│
├── myenv/                               # Python virtual environment
│   ├── pyvenv.cfg
│   ├── Include/
│   ├── Lib/
│   │   └── site-packages/               # Dependencies: FastAPI, SQLAlchemy, Pandas, etc.
│   └── Scripts/
│
├── requirements.txt                     # Python dependencies
└── readme.md                            # Project documentation
```

**Key Directories Explained:**

- **`app/api/`** - API route handlers
  - `v1/` - v1 API endpoints (stocks, comparisons, etc.)
- **`app/core/`** - Core infrastructure
  - `config.py` - Environment and database configuration
  - `db.py` - SQLAlchemy engine, session factory, Base model
  - `schema_sync.py` - Idempotent schema initialization, migrations, FK creation
- **`app/models/`** - SQLAlchemy ORM definitions
  - Supports split-table pattern: `StockPrice` (raw) + `StockFeature` (derived)
  - Composite foreign keys with timestamps and proper data types
- **`app/pipelines/`** - ETL workflow
  - `fetcher.py` - Yahoo Finance & AlphaVantage with fallback chain
  - `cleaner.py` - Validation and outlier detection
  - `transformer.py` - Feature engineering (MA7, daily returns, etc.)
  - `loader.py` - Upsert to split tables with conflict handling
- **`app/repositories/`** - Data access layer
  - Explicit INNER JOINs between raw and derived tables
  - `StockJoinedRow` adapter maintains API backward compatibility
- **`app/services/`** - Business logic with single responsibility
  - `market_data_service.py` - Data fetching and normalization
  - `signal_service.py` - Trading signal generation
  - `prediction_service.py` - Price predictions
  - `ai_service.py` - AI insights and analysis
  - `stock_service.py` - Orchestration layer
- **`app/utils/`** - Shared utilities
  - `cache.py` - In-memory TTL cache with prefix-scoped invalidation

**Architecture Patterns:**

- **Repository Pattern**: All data access through `stock_repository.py` with explicit joins
- **Service Layer**: Business logic isolated from API/persistence
- **Split-Table Pattern**: Raw immutable prices + recomputable features
- **Provider Factory**: Fallback chain for robust data fetching
- **Prefix-Scoped Caching**: Granular cache invalidation by data category

## Tech Stack

**Backend:**
- Framework: FastAPI
- Language: Python 3.11+
- ORM: SQLAlchemy 2.0+
- Database: PostgreSQL (production) / SQLite (development)
- Data Processing: Pandas, NumPy
- API Clients: requests, BeautifulSoup4
- Validation: Pydantic

**Frontend:**
- Framework: Next.js 14
- Language: TypeScript 5.0+
- UI Library: Shadcn/ui
- Styling: Tailwind CSS
- Data Fetching: SWR
- Charts: Chart.js
- Icons: Lucide Icons

**DevOps:**
- API Server: Uvicorn
- Package Manager: pip
- Environment: Python venv

## Architecture Highlights

**Data Model:**
```
StockPrice (Raw, Immutable)
├── symbol (string)
├── date (datetime)
├── open, high, low, close, volume (BigInteger)
├── created_at, updated_at (timestamps)
└── → StockFeature (1-to-1)

StockFeature (Derived, Recomputable)
├── symbol (string)
├── date (datetime)
├── daily_return, ma7, ma20, volatility (nullable)
├── created_at, updated_at (timestamps)
└── ← StockPrice (composite FK)
```

**Service Layer:**
- **market_data_service**: Fetches and normalizes OHLCV data
- **signal_service**: Generates buy/sell signals from indicators
- **prediction_service**: Predicts future prices
- **ai_service**: Advanced analytics and insights
- **stock_service**: Orchestrates all services

**Caching Strategy:**
- Prefix-scoped invalidation (e.g., `market:INFY`, `signal:INFY`)
- Sub-key granularity for time-based data
- Prevents accidental cache clearing of unrelated entries

## Getting Started

### Prerequisites
- Python 3.11+
- pip or virtual environment
- PostgreSQL (optional, SQLite supported)
- Node.js 18+ (for frontend only)

### Backend Setup

```bash
# Navigate to project root
cd c:\Users\INFINIX\Desktop\stock-dashboard

# Create and activate virtual environment
python -m venv myenv
myenv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
# Create .env file with:
# DATABASE_URL=sqlite:///./stock.db
# or
# DATABASE_URL=postgresql://user:password@localhost:5432/stock_db

# Initialize database schema
python -c "from app.core.db import init_db; init_db()"

# Run backend server
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd stock-dashboard-frontend

# Install dependencies
npm install
# or
pnpm install

# Start development server
npm run dev
# Frontend available at http://localhost:3000
```

### Running the Pipeline

```bash
# Fetch and process stock data
python scripts/run_pipeline.py

# Or from Python:
# from app.pipelines.fetcher import fetch_stock_data
# from app.pipelines.cleaner import clean_stock_data
# from app.pipelines.transformer import transform_stock_data
# from app.pipelines.loader import load_to_db
```

## API Endpoints

**Stock Data:**
- `GET /api/v1/stocks/{symbol}/data` - Get historical stock data
- `GET /api/v1/stocks/{symbol}/latest` - Get latest price point
- `GET /api/v1/stocks/movers/top` - Get top movers

**Response Schema:**
```typescript
{
  symbol: string;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: integer;          // BigInteger for precision
  daily_return?: number;    // Nullable derived metric
  ma7?: number;            // Nullable derived metric
  ma20?: number;           // Nullable derived metric
  created_at: string;
  updated_at: string;
}
```

## Database Schema

**Production Features:**
- Composite foreign keys with ON DELETE CASCADE
- BigInteger volume (no precision loss)
- Timestamps on all tables (created_at, updated_at)
- Descending date indexes for efficient time-series queries
- Idempotent schema migrations (supports both PostgreSQL and SQLite)

**Schema Sync:**
The `schema_sync.py` module handles:
- Split-table creation and initialization
- Timestamp backfill for existing records
- Foreign key constraint creation (PostgreSQL)
- Idempotent volume type migration

## Development Workflow

1. **Fetch Data**: `app/pipelines/fetcher.py` retrieves from Yahoo/AlphaVantage
2. **Clean Data**: `app/pipelines/cleaner.py` validates and detects outliers
3. **Transform Data**: `app/pipelines/transformer.py` creates derived features
4. **Load Data**: `app/pipelines/loader.py` upserts to split tables
5. **Access Data**: `app/repositories/stock_repository.py` with explicit joins
6. **Business Logic**: Services normalize and process for API
7. **API Response**: Pydantic schemas serialize to frontend
8. **Frontend Display**: Next.js renders with SWR data fetching and Chart.js

## Best Practices

- ✅ Keep data immutable in `StockPrice` table
- ✅ Recompute features in `StockFeature` if calculation logic changes
- ✅ Use prefix-scoped cache invalidation for granular control
- ✅ Leverage repository joins instead of raw SQL
- ✅ Add tests for service boundaries (market/signal/prediction/ai)
- ✅ Use strict INNER JOINs for consistency
- ✅ Maintain type safety between backend and frontend schemas

## License

This project is licensed under the MIT License.  
Copyright (c) 2025 Stock Dashboard

---

**Questions or Issues?** Open an issue or submit a pull request!
