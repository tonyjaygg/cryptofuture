from __future__ import annotations

import asyncio

from exchanges.mexc import MexcClient
from strategies.momentum_ema import MomentumEMAStrategy
from core.models import Order


async def run(symbol: str) -> None:
    client = MexcClient()
    data = client.kline(symbol, "1m")
    closes = [float(k[4]) for k in data]
    df = {
        'close': closes
    }
    import pandas as pd
    df = pd.DataFrame(df)
    strat = MomentumEMAStrategy()
    signal = strat.generate(df).iloc[-1]
    if signal == 1:
        order = Order(symbol=symbol, side='buy', qty=1)
    elif signal == -1:
        order = Order(symbol=symbol, side='sell', qty=1)
    else:
        order = None
    if order:
        from loguru import logger
        logger.info(f"Would place order: {order}")
    client.close()


if __name__ == "__main__":
    asyncio.run(run("BTCUSDT"))
