from app.services.ai_service import fetch_ai_chat_response, fetch_ai_stock_explanation
from app.services.market_data_service import (
    compare_stocks,
    fetch_stock_data,
    fetch_stock_summary,
    fetch_top_gainers,
    fetch_top_losers,
    list_companies,
)
from app.services.prediction_service import fetch_prediction
from app.services.signal_service import fetch_signal, fetch_stock_explanation