from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class RiskState:
    daily_loss: float = 0.0
    last_day: date | None = None


class RiskManager:
    def __init__(self, max_daily_loss_pct: float, balance: float) -> None:
        self.max_daily_loss_pct = max_daily_loss_pct
        self.balance = balance
        self.state = RiskState()

    def check_daily(self) -> bool:
        today = date.today()
        if self.state.last_day != today:
            self.state = RiskState(last_day=today)
        limit = self.balance * self.max_daily_loss_pct
        return self.state.daily_loss < limit

    def register_loss(self, loss: float) -> None:
        self.state.daily_loss += loss
