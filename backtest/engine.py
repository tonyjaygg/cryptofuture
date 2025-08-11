from __future__ import annotations

import pandas as pd

from core.models import Order, Portfolio
from strategies.momentum_ema import MomentumEMAStrategy


class BacktestEngine:
    def __init__(self, data: pd.DataFrame, strategy: MomentumEMAStrategy) -> None:
        self.data = data
        self.strategy = strategy
        self.portfolio = Portfolio(cash=10000)

    def run(self) -> Portfolio:
        signals = self.strategy.generate(self.data)
        for idx, signal in signals.iteritems():
            price = self.data.loc[idx, 'close']
            if signal == 1:
                order = Order(symbol='MEXC', side='buy', qty=1, price=price)
                self.portfolio.update_fill(order, price)
            elif signal == -1:
                order = Order(symbol='MEXC', side='sell', qty=1, price=price)
                self.portfolio.update_fill(order, price)
        return self.portfolio
