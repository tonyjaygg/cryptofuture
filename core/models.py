from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Order(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    qty: float
    price: float | None = None
    type: Literal["limit", "market"] = "market"
    id: str | None = None


class Position(BaseModel):
    symbol: str
    qty: float = 0
    entry_price: float = 0

    def update(self, fill_qty: float, fill_price: float) -> None:
        new_qty = self.qty + fill_qty
        if new_qty == 0:
            self.qty = 0
            self.entry_price = 0
            return
        self.entry_price = (
            self.entry_price * self.qty + fill_price * fill_qty
        ) / new_qty
        self.qty = new_qty


class Portfolio(BaseModel):
    cash: float = 0
    positions: dict[str, Position] = Field(default_factory=dict)

    def update_fill(self, order: Order, fill_price: float) -> None:
        cost = fill_price * order.qty
        if order.side == "buy":
            self.cash -= cost
            qty = order.qty
        else:
            self.cash += cost
            qty = -order.qty
        pos = self.positions.get(order.symbol, Position(symbol=order.symbol))
        pos.update(qty, fill_price)
        self.positions[order.symbol] = pos
