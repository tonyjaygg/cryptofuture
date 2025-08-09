# Crypto Futures Trading Bot

This project provides an example Python bot for trading MEXC perpetual futures.
It fetches market data, calculates indicators and executes trades based on a
simple rule set. The bot includes basic risk management, logging and Telegram
notifications.

## Features
- Connects to MEXC via `ccxt`
- Uses EMA, RSI, MACD and Bollinger Bands for signal generation
- Configurable leverage, stop loss, take profit and trailing stop
- Daily loss limit and position sizing by percentage of equity
- Logs all activity to `bot.log`

## Installation
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running
Set your API credentials as environment variables and run the bot:
```bash
export MEXC_API_KEY="<key>"
export MEXC_API_SECRET="<secret>"
python mexc_futures_bot.py
```
Optional variables:
- `MEXC_SYMBOL` (default `BTC/USDT:USDT`)
- `MEXC_LEVERAGE` (default `5`)

## Backtesting
The provided script focuses on live trading. For strategy evaluation, extend
it with historical data testing using the same indicator logic.

## Parameter tuning
- Increase `tp_pct` / decrease `sl_pct` for more aggressive profit targets.
- Adjust `risk_per_trade` to control position sizing.
- `max_daily_loss_pct` acts as a kill switch for bad trading days.

Use these settings in conjunction with your own market analysis to balance
profit potential against acceptable risk.
