from __future__ import annotations

import pandas as pd
import pandas_ta as ta


class MomentumEMAStrategy:
    def __init__(self, fast: int = 20, slow: int = 50) -> None:
        self.fast = fast
        self.slow = slow

    def generate(self, df: pd.DataFrame) -> pd.Series:
        ema_fast = ta.ema(df['close'], self.fast)
        ema_slow = ta.ema(df['close'], self.slow)
        signal = (ema_fast > ema_slow).astype(int) - (ema_fast < ema_slow).astype(int)
        return signal
