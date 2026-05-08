# Challenge BOT - TopstepX EMA/ATR Trading Evaluation Bot

A Python-based automated trading bot for TopstepX futures challenges using EMA crossover signals with ATR-based position sizing and risk management.

## Features

- **Strategy**: EMA (9/21) crossover with price action confirmation
- **Position Sizing**: ATR-based dynamic bracket calculation
- **Risk Management**:
  - Daily loss limit with account lockout
  - Max trades per day limit
  - Manual pause control
  - News event pause windows
  - End-of-day position flattening
  - One-trade-at-a-time safety guard
  
- **Market Access**: Support for NQ, ES, MES, MGC contracts
- **Flexible**: Paper trading (simulation) or live trading modes

## Installation

### Prerequisites
- Python 3.10+
- TopstepX API credentials

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/johnmdefilippo-rgb/Challenge-BOT.git
   cd Challenge-BOT
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure credentials**
   - Edit `config.py`
   - Add your TopstepX username and API key
   - Set your account ID
   - Adjust strategy parameters as needed

## Configuration

Edit `config.py` to customize:

### API & Account
```python
"username": "YOUR_USERNAME",        # TopstepX username
"api_key": "YOUR_API_KEY",          # TopstepX API key
"account_id": 123456,               # Your account ID
```

### Strategy Parameters
```python
"symbol": "NQ",                     # Contract symbol (NQ, ES, MES, MGC)
"live": False,                      # False = paper trading, True = live
"ema_fast": 9,                      # Fast EMA period
"ema_slow": 21,                     # Slow EMA period
"atr_length": 14,                   # ATR period for brackets
"atr_tp_multiplier": 1.0,           # Take-profit multiplier of ATR
"atr_sl_multiplier": 1.0,           # Stop-loss multiplier of ATR
```

### Risk Controls
```python
"max_trades_per_day": 3,            # Maximum trades in a trading day
"daily_loss_limit": 1000.00,        # Stop trading if loss exceeds this
"one_trade_at_a_time": True,        # Prevent overlapping positions
"manual_pause": False,              # Pause trading without stopping bot
```

### Trading Hours (Eastern Time)
```python
"trading_start_et": "09:35",        # Start accepting signals
"trading_end_et": "15:45",          # Stop accepting new signals
"no_new_trades_after_et": "15:30",  # Final cutoff for new trades
"flatten_time_et": "15:50",         # Force close all positions
```

### News Pause (Optional)
```python
"news_pause_enabled": False,
"blocked_news_windows": [
    {"start_et": "09:55", "end_et": "10:10", "reason": "High impact news"}
]
```

## Running the Bot

```bash
python bot.py
```

The bot will:
1. Authenticate with TopstepX
2. Load market data and calculate indicators
3. Monitor for EMA crossover signals
4. Execute trades with ATR-based brackets
5. Enforce all risk management rules
6. Run continuously until stopped (Ctrl+C)

## Trading Logic

### Entry Signal
The bot generates a LONG signal when:
- Price crosses above both EMA Fast AND EMA Slow
- This crossover didn't exist in the previous bar
- EMA Fast is above EMA Slow (bullish structure)

The bot generates a SHORT signal when:
- Price crosses below both EMA Fast AND EMA Slow
- This crossover didn't exist in the previous bar
- EMA Fast is below EMA Slow (bearish structure)

### Position Management
- **Take Profit**: ATR × TP Multiplier ÷ Tick Size = ticks
- **Stop Loss**: ATR × SL Multiplier ÷ Tick Size = ticks (if enabled)
- **Size**: (Evaluation Size ÷ 50,000) × Contracts Per 50k

### Risk Controls Applied In Order
1. Manual pause check
2. Daily loss limit lockout
3. Trading hours validation
4. No-new-trades cutoff check
5. Max trades per day limit
6. News event pause windows
7. One-trade-at-a-time guard
8. Open order check

## Security

⚠️ **IMPORTANT**: Never commit `config.py` with real credentials to public repositories.

- Add credentials to `config.py` (not tracked by git)
- Use environment variables for production deployments
- The `.gitignore` file protects sensitive data

## Troubleshooting

### "Authentication failed"
- Verify username and API key in `config.py`
- Check TopstepX API is responding

### "Contract search failed"
- Confirm symbol exists (NQ, ES, MES, MGC)
- Verify `live` parameter matches your account type

### "No historical bars returned"
- Market may be closed
- Insufficient data for the requested timeframe

### "Account balance field not found"
- API may return unexpected account data structure
- Check TopstepX API documentation
- May need to adjust `get_account_balance()` method

## Files Structure

```
Challenge-BOT/
├── bot.py                   # Main bot implementation
├── config.py                # Configuration (edit this!)
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Performance Tips

1. **Adjust EMA periods** to match your trading style
2. **Fine-tune ATR multipliers** for optimal risk/reward
3. **Set realistic daily loss limits** for your account
4. **Test with paper trading** before going live
5. **Monitor logs** for pattern analysis

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review TopstepX API documentation
3. Verify configuration settings
4. Ensure market hours alignment

## License

This project is provided as-is for educational purposes.

## Disclaimer

This is a trading bot for futures. Trading involves substantial risk of loss. Past performance does not guarantee future results. Always paper trade first and use appropriate risk management.
