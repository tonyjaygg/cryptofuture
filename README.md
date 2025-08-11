# CryptoFuture Bot

Autopilot MEXC futures trading bot.

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Run first-time autoconfig to create `.env` and config:
```bash
python cli/bot.py autoconfig
```

Start paper trading:
```bash
python cli/bot.py paper BTCUSDT
```

Backtest with CSV data:
```bash
python cli/bot.py backtest --symbol BTCUSDT --csv data.csv
```

Live run (requires keys in `.env`):
```bash
python cli/bot.py live BTCUSDT
```
