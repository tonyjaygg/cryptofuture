from __future__ import annotations

import asyncio
from datetime import datetime

from loguru import logger


async def run(symbol: str) -> None:
    """Very small paper trading loop printing ticks"""
    logger.info("Starting paper mode for {}", symbol)
    for i in range(5):
        logger.info("paper tick {} {}", symbol, datetime.utcnow())
        await asyncio.sleep(1)
    logger.info("paper session finished")
