from __future__ import annotations

import os
from typing import Any

import httpx
from loguru import logger


class MexcClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("MEXC_API_KEY", "")
        self.api_secret = os.getenv("MEXC_API_SECRET", "")
        self.client = httpx.Client(base_url="https://api.mexc.com")

    def kline(self, symbol: str, interval: str) -> Any:
        resp = self.client.get(
            "/api/v3/klines", params={"symbol": symbol, "interval": interval}
        )
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self.client.close()
