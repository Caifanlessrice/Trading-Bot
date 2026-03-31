"""
Entry point for paper trading (simulated live trading — no real money).

Usage examples:
  python run_paper_trade.py --ticker AAPL --strategy trend
  python run_paper_trade.py --ticker AAPL --strategy mean
  python run_paper_trade.py --ticker MSFT --strategy trend --config config/settings.yaml

The bot will:
  1. Load recent history for indicator warmup
  2. Evaluate entry/exit signals on the current bar
  3. Simulate fills with fake money
  4. Print a live performance summary
  5. Repeat every N minutes (set check_interval_minutes in config/settings.yaml)

Press Ctrl+C to stop and see the final session summary.
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from utils.config_loader import ConfigLoader
from paper_trading.engine import PaperEngine


def parse_args():
    parser = argparse.ArgumentParser(description="Run a paper trading session.")
    parser.add_argument("--ticker",   required=True, help="Stock ticker symbol, e.g. AAPL")
    parser.add_argument("--strategy", required=True, choices=["trend", "mean"],
                        help="Strategy to use: trend | mean")
    parser.add_argument("--config",   default="config/settings.yaml", help="Path to settings YAML")
    return parser.parse_args()


def main():
    args = parse_args()

    loader = ConfigLoader()
    config = loader.load(args.config)

    engine = PaperEngine(config, ticker=args.ticker, strategy_name=args.strategy)
    engine.start()


if __name__ == "__main__":
    main()
