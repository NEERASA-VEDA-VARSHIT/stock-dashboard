from app.core.config import STOCK_PROVIDER_FALLBACK, STOCK_PROVIDER_PRIMARY
from app.providers.alpha_vantage_provider import AlphaVantageProvider
from app.providers.base import StockProvider
from app.providers.yahoo_provider import YahooProvider


def get_provider(name: str) -> StockProvider:
    normalized = (name or "").strip().lower()
    if normalized == "yahoo":
        return YahooProvider()
    if normalized == "alpha_vantage":
        return AlphaVantageProvider()
    raise ValueError(f"Unsupported provider '{name}'")


def get_provider_chain() -> list[StockProvider]:
    names = [STOCK_PROVIDER_PRIMARY, STOCK_PROVIDER_FALLBACK]
    providers: list[StockProvider] = []
    seen = set()

    for name in names:
        if not name or name in seen:
            continue
        seen.add(name)
        providers.append(get_provider(name))

    if not providers:
        providers.append(YahooProvider())
    return providers


def fetch_with_fallback(symbol: str, period: str = "1y"):
    last_error = None
    for provider in get_provider_chain():
        try:
            data = provider.fetch(symbol=symbol, period=period)
            if data is None or data.empty:
                raise ValueError(f"No data found for {symbol} from provider '{provider.name}'")
            return data, provider.name
        except Exception as exc:
            last_error = exc
    raise ValueError(f"No provider could fetch data for {symbol}: {last_error}")
