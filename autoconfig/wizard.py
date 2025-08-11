from __future__ import annotations

import os
import stat
from getpass import getpass
from pathlib import Path
from typing import List

import httpx
import pandas as pd
import yaml

from backtest.engine import BacktestEngine
from strategies.momentum_ema import MomentumEMAStrategy

DATA_DIR = Path("data")
CONF_DIR = Path("conf")


def _write_env(key: str, secret: str) -> None:
    env_path = Path(".env")
    env_path.write_text(f"MEXC_API_KEY={key}\nMEXC_API_SECRET={secret}\n")
    os.chmod(env_path, stat.S_IRUSR | stat.S_IWUSR)


def ensure_env() -> tuple[str, str]:
    key = os.getenv("MEXC_API_KEY")
    secret = os.getenv("MEXC_API_SECRET")
    if key and secret:
        return key, secret
    key = getpass("MEXC API KEY: ")
    secret = getpass("MEXC API SECRET: ")
    _write_env(key, secret)
    return key, secret


async def fetch_symbols(client: httpx.AsyncClient) -> List[str]:
    r = await client.get("https://contract.mexc.com/api/v1/contract/ticker")
    r.raise_for_status()
    data = r.json().get("data", [])
    data.sort(key=lambda x: float(x.get("vol24", 0)), reverse=True)
    return [d["symbol"] for d in data[:2]]


async def fetch_kline(client: httpx.AsyncClient, symbol: str) -> pd.DataFrame:
    url = f"https://contract.mexc.com/api/v1/contract/kline/{symbol}?interval=1m&limit=1000"
    r = await client.get(url)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["data"], columns=["ts","o","h","l","c","v"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    df.rename(columns={"o":"open","h":"high","l":"low","c":"close","v":"volume"}, inplace=True)
    DATA_DIR.mkdir(exist_ok=True)
    df.to_parquet(DATA_DIR / f"{symbol}_1m.parquet")
    return df


async def run() -> None:
    ensure_env()
    async with httpx.AsyncClient() as client:
        symbols = await fetch_symbols(client)
        chosen = None
        best = -1.0
        for sym in symbols:
            df = await fetch_kline(client, sym)
            strat = MomentumEMAStrategy()
            engine = BacktestEngine(df, strat)
            portfolio = engine.run()
            value = portfolio.cash
            if value > best:
                chosen = sym
                best = value
        CONF_DIR.mkdir(exist_ok=True)
        conf = {"symbol": chosen, "strategy": "MOMENTUM_EMA"}
        (CONF_DIR / "autogen.yml").write_text(yaml.safe_dump(conf))
        print(f"Generated conf/autogen.yml for {chosen}")
