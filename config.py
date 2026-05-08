from zoneinfo import ZoneInfo

# ============================================================
# CONFIG
# ============================================================

CONFIG = {
    # TopstepX credentials
    "username": "YOUR_USERNAME",
    "api_key": "YOUR_API_KEY",

    # Account
    "account_id": 123456,

    # Evaluation sizing
    "evaluation_size": 50000,
    "contracts_per_50k": 2,

    # Market selection
    "symbol": "NQ",  # NQ, ES, MES, MGC
    "live": False,

    # Strategy
    "timeframe_minutes": 2,
    "ema_fast": 9,
    "ema_slow": 21,
    "atr_length": 14,

    # ATR brackets
    "atr_tp_multiplier": 1.0,
    "use_stop_loss": True,
    "atr_sl_multiplier": 1.0,

    # Risk controls
    "manual_pause": False,
    "one_trade_at_a_time": True,
    "max_trades_per_day": 3,
    "daily_loss_limit": 1000.00,

    # Trading session controls - Eastern time
    "trading_start_et": "09:35",
    "trading_end_et": "15:45",
    "no_new_trades_after_et": "15:30",

    # End-of-day protection
    "flatten_at_end_of_day": True,
    "flatten_time_et": "15:50",

    # News pause placeholder
    "news_pause_enabled": False,
    "blocked_news_windows": [
        # Example:
        # {"start_et": "09:55", "end_et": "10:10", "reason": "High impact news"}
    ],
}

# API Configuration
API_ENDPOINT = "https://api.topstepx.com"
EASTERN_TZ = ZoneInfo("America/New_York")
