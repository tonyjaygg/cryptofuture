import os
import time
import logging
from dataclasses import dataclass
from typing import Optional

import ccxt
import pandas as pd
import requests
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands


@dataclass
class BotConfig:
    """Configuration for the trading bot."""

    api_key: str
    api_secret: str
    symbol: str = "BTC/USDT:USDT"  # MEXC perpetual futures symbol
    leverage: int = 5
    timeframe: str = "1m"
    trend_timeframe: str = "15m"
    max_daily_loss_pct: float = 0.05
    risk_per_trade: float = 0.01
    sl_pct: float = 0.005
    tp_pct: float = 0.01
    trailing_stop_pct: float = 0.004
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None


def init_exchange(cfg: BotConfig) -> ccxt.mexc:
    """Initialise the MEXC exchange client."""
    exchange = ccxt.mexc({
        "apiKey": cfg.api_key,
        "secret": cfg.api_secret,
        "options": {"defaultType": "swap"},  # use futures
    })
    exchange.set_leverage(cfg.leverage, cfg.symbol)
    return exchange


def fetch_ohlcv(exchange: ccxt.mexc, symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
    data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ema_fast"] = EMAIndicator(df["close"], window=9).ema_indicator()
    df["ema_slow"] = EMAIndicator(df["close"], window=21).ema_indicator()
    macd = MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()
    df["rsi"] = RSIIndicator(df["close"], window=14).rsi()
    bb = BollingerBands(df["close"], window=20, window_dev=2)
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()
    return df


def generate_signal(df: pd.DataFrame) -> Optional[str]:
    """Generate trading signal based on indicators."""
    last = df.iloc[-1]
    if (
        last["close"] > last["ema_fast"] > last["ema_slow"]
        and last["macd_hist"] > 0
        and last["close"] > last["bb_high"]
    ):
        return "long"
    if (
        last["close"] < last["ema_fast"] < last["ema_slow"]
        and last["macd_hist"] < 0
        and last["close"] < last["bb_low"]
    ):
        return "short"
    if last["rsi"] < 30 and last["close"] > last["bb_low"]:
        return "long"
    if last["rsi"] > 70 and last["close"] < last["bb_high"]:
        return "short"
    return None


def determine_trend(df: pd.DataFrame) -> str:
    """Determine higher timeframe trend using EMA crossover."""
    last = df.iloc[-1]
    return "long" if last["ema_fast"] > last["ema_slow"] else "short"


def position_size(balance: float, risk_pct: float, entry: float, stop: float, leverage: int) -> float:
    risk_amount = balance * risk_pct
    diff = abs(entry - stop)
    if diff == 0:
        return 0.0
    size = risk_amount / diff * leverage
    return size


def send_telegram(cfg: BotConfig, message: str) -> None:
    if not cfg.telegram_token or not cfg.telegram_chat_id:
        return
    url = f"https://api.telegram.org/bot{cfg.telegram_token}/sendMessage"
    payload = {"chat_id": cfg.telegram_chat_id, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception:  # pragma: no cover - network errors ignored
        pass


def trade_loop(cfg: BotConfig) -> None:
    logging.basicConfig(
        filename="bot.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    exchange = init_exchange(cfg)
    start_equity = float(exchange.fetch_balance()["USDT"]["total"])
    daily_loss_limit = start_equity * cfg.max_daily_loss_pct

    position = None

    while True:
        df = fetch_ohlcv(exchange, cfg.symbol, cfg.timeframe)
        df = compute_indicators(df)
        last_price = df.iloc[-1]["close"]
        signal = generate_signal(df)
        df_trend = compute_indicators(fetch_ohlcv(exchange, cfg.symbol, cfg.trend_timeframe))
        trend = determine_trend(df_trend)

        if position:
            if position["side"] == "long":
                position["sl"] = max(position["sl"], last_price * (1 - cfg.trailing_stop_pct))
                if last_price <= position["sl"]:
                    exchange.create_order(cfg.symbol, "market", "sell", position["size"])
                    logging.info("Trailing stop hit, closing long")
                    position = None
                    continue
            else:
                position["sl"] = min(position["sl"], last_price * (1 + cfg.trailing_stop_pct))
                if last_price >= position["sl"]:
                    exchange.create_order(cfg.symbol, "market", "buy", position["size"])
                    logging.info("Trailing stop hit, closing short")
                    position = None
                    continue

        if signal and not position and signal == trend:
            balance = float(exchange.fetch_balance()["USDT"]["total"])
            sl = last_price * (1 - cfg.sl_pct) if signal == "long" else last_price * (1 + cfg.sl_pct)
            tp = last_price * (1 + cfg.tp_pct) if signal == "long" else last_price * (1 - cfg.tp_pct)
            size = position_size(balance, cfg.risk_per_trade, last_price, sl, cfg.leverage)
            params = {
                "stopLossPrice": sl,
                "takeProfitPrice": tp,
            }
            try:
                order = exchange.create_order(cfg.symbol, "market", signal, size, params=params)
                logging.info("%s order executed: %s", signal, order)
                send_telegram(cfg, f"Order {signal} size {size} at {last_price}")
                position = {"side": signal, "size": size, "sl": sl}
            except Exception as exc:  # pragma: no cover - network errors ignored
                logging.error("Order failed: %s", exc)

        current_equity = float(exchange.fetch_balance()["USDT"]["total"])
        if start_equity - current_equity > daily_loss_limit:
            logging.warning("Daily loss limit reached. Stopping trading for the day.")
            send_telegram(cfg, "Daily loss limit reached. Bot paused.")
            break
        time.sleep(30)


def main() -> None:
    cfg = BotConfig(
        api_key=os.getenv("MEXC_API_KEY", ""),
        api_secret=os.getenv("MEXC_API_SECRET", ""),
        symbol=os.getenv("MEXC_SYMBOL", "BTC/USDT:USDT"),
        leverage=int(os.getenv("MEXC_LEVERAGE", "5")),
    )
    trade_loop(cfg)


if __name__ == "__main__":
    main()
