from __future__ import annotations

import argparse
import asyncio

import pandas as pd

from autoconfig.wizard import run as autoconfig_run
from backtest.engine import BacktestEngine
from paper.runner import run as paper_run
from strategies.momentum_ema import MomentumEMAStrategy
from live.runner import run as live_run


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("autoconfig")

    bt = sub.add_parser("backtest")
    bt.add_argument("--csv", required=True)
    bt.add_argument("--symbol", required=True)

    pp = sub.add_parser("paper")
    pp.add_argument("symbol")

    lv = sub.add_parser("live")
    lv.add_argument("symbol")

    args = parser.parse_args()

    if args.cmd == "autoconfig":
        asyncio.run(autoconfig_run())
    elif args.cmd == "backtest":
        df = pd.read_csv(args.csv)
        strat = MomentumEMAStrategy()
        engine = BacktestEngine(df, strat)
        portfolio = engine.run()
        print(portfolio)
    elif args.cmd == "paper":
        asyncio.run(paper_run(args.symbol))
    elif args.cmd == "live":
        asyncio.run(live_run(args.symbol))


if __name__ == "__main__":
    main()
