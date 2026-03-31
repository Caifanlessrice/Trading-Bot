"""
Entry point for backtesting.

Usage examples:
  python run_backtest.py --ticker AAPL --strategy trend
  python run_backtest.py --ticker AAPL --strategy mean
  python run_backtest.py --ticker AAPL --strategy both
  python run_backtest.py --ticker MSFT --strategy trend --start 2022-01-01 --end 2024-12-31
  python run_backtest.py --ticker AAPL --strategy trend --plot
  python run_backtest.py --ticker AAPL --strategy trend --optimize
"""

import argparse
import sys
import os

# Allow imports from the trading-bot root
sys.path.insert(0, os.path.dirname(__file__))

from utils.config_loader import ConfigLoader
from data.fetcher import DataFetcher
from backtest.runner import BacktestRunner
from backtest.reporter import Reporter


def parse_args():
    parser = argparse.ArgumentParser(description="Run a backtest on a US equity.")
    parser.add_argument("--ticker",   required=True,  help="Stock ticker symbol, e.g. AAPL")
    parser.add_argument("--strategy", required=True,  choices=["trend", "mean", "both"],
                        help="Strategy to run: trend | mean | both")
    parser.add_argument("--start",    default=None,   help="Start date YYYY-MM-DD (overrides config)")
    parser.add_argument("--end",      default=None,   help="End date YYYY-MM-DD (overrides config)")
    parser.add_argument("--config",   default="config/settings.yaml", help="Path to settings YAML")
    parser.add_argument("--optimize", action="store_true", help="Run parameter optimisation")
    parser.add_argument("--plot",     action="store_true", help="Show interactive chart after run")
    return parser.parse_args()


def main():
    args = parse_args()

    loader = ConfigLoader()
    config = loader.load(args.config)

    bt_cfg = config["backtest"]
    start = args.start or bt_cfg["start_date"]
    end   = args.end   or bt_cfg["end_date"]

    # Override plot setting from CLI flag
    if args.plot:
        config["output"]["plot_show"] = True

    fetcher = DataFetcher()
    data = fetcher.fetch(args.ticker, start, end, bt_cfg["data_interval"])

    runner   = BacktestRunner(config)
    reporter = Reporter(config)

    strategy_names = ["trend", "mean"] if args.strategy == "both" else [args.strategy]

    if args.optimize and args.strategy == "both":
        print("--optimize is only supported for a single strategy. Use --strategy trend or --strategy mean.")
        sys.exit(1)

    if args.optimize:
        name = strategy_names[0]
        param_grid = _build_param_grid(name, config)
        print(f"\nRunning optimisation for '{name}' on {args.ticker} …")
        stats, heatmap = runner.optimize(name, data, param_grid)
        reporter.print_summary(stats, _label(name, config), args.ticker, start, end)
        print("\nOptimisation heatmap (top parameters):")
        print(heatmap.sort_values(ascending=False).head(10).to_string())
        return

    results = {}
    for name in strategy_names:
        print(f"\nRunning '{name}' strategy on {args.ticker} ({start} → {end}) …")
        stats = runner.run(name, data)
        results[name] = stats
        reporter.print_summary(stats, _label(name, config), args.ticker, start, end)
        reporter.save_results(stats, name, args.ticker)

        if args.plot and len(strategy_names) == 1:
            # backtesting.py plot — opens a browser tab
            from backtesting import Backtest
            from backtest.runner import STRATEGY_MAP
            strategy_class = STRATEGY_MAP[name]
            runner._inject_config(strategy_class, name)
            bt = Backtest(data, strategy_class,
                          cash=config["backtest"]["initial_cash"],
                          commission=config["backtest"]["commission"],
                          exclusive_orders=True)
            bt.run()
            bt.plot()

    if args.strategy == "both":
        reporter.compare_strategies(results, args.ticker, start, end)


def _label(name: str, config: dict) -> str:
    if name == "trend":
        cfg = config["trend_following"]
        return f"Trend Following ({cfg['ma_type'].upper()} {cfg['fast_period']}/{cfg['slow_period']})"
    elif name == "mean":
        cfg = config["mean_reversion"]
        return f"Mean Reversion (RSI {cfg['rsi_period']})"
    return name


def _build_param_grid(name: str, config: dict) -> dict:
    """Default parameter sweep grid for optimisation."""
    if name == "trend":
        return {
            "fast_period": range(10, 31, 5),
            "slow_period": range(40, 101, 10),
        }
    elif name == "mean":
        return {
            "rsi_oversold":  range(20, 36, 5),
            "rsi_overbought": range(65, 81, 5),
        }
    return {}


if __name__ == "__main__":
    main()
