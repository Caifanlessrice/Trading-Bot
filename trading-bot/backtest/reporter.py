import os
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


class Reporter:
    def __init__(self, config: dict):
        self._output_cfg = config.get("output", {})
        self._results_dir = Path(self._output_cfg.get("results_dir", "results"))
        self._results_dir.mkdir(parents=True, exist_ok=True)

    def print_summary(self, stats, strategy_name: str, ticker: str, start: str, end: str) -> None:
        """Print a formatted performance table to the console."""
        table = Table(
            title=f"[bold cyan]{strategy_name}[/bold cyan]  ·  {ticker}  ·  {start} → {end}",
            box=box.DOUBLE_EDGE,
            show_header=False,
            padding=(0, 2),
        )
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right", style="bold white")

        def _pct(val):
            if val is None:
                return "N/A"
            color = "green" if val >= 0 else "red"
            return f"[{color}]{val:+.1f}%[/{color}]"

        def _float(val, decimals=2):
            if val is None:
                return "N/A"
            return f"{val:.{decimals}f}"

        def _int(val):
            return str(int(val)) if val is not None else "N/A"

        rows = [
            ("Total Return",          _pct(stats.get("Return [%]"))),
            ("Buy & Hold Return",     _pct(stats.get("Buy & Hold Return [%]"))),
            ("Sharpe Ratio",          _float(stats.get("Sharpe Ratio"))),
            ("Sortino Ratio",         _float(stats.get("Sortino Ratio"))),
            ("Max Drawdown",          _pct(stats.get("Max. Drawdown [%]"))),
            ("Win Rate",              _pct(stats.get("Win Rate [%]"))),
            ("# Trades",              _int(stats.get("# Trades"))),
            ("Best Trade",            _pct(stats.get("Best Trade [%]"))),
            ("Worst Trade",           _pct(stats.get("Worst Trade [%]"))),
            ("Avg Trade Duration",    str(stats.get("Avg. Trade Duration", "N/A"))),
        ]

        for metric, value in rows:
            table.add_row(metric, value)

        console.print()
        console.print(table)

    def save_results(self, stats, strategy_name: str, ticker: str) -> str:
        """Save stats to a timestamped CSV. Returns the file path."""
        if not self._output_cfg.get("save_csv", True):
            return ""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ticker}_{strategy_name}_{timestamp}.csv"
        filepath = self._results_dir / filename
        stats_series = stats._series if hasattr(stats, "_series") else None
        # Save the equity curve if available
        if stats_series is not None:
            stats_series.to_csv(filepath)
        else:
            import pandas as pd
            pd.Series(dict(stats)).to_csv(filepath)
        console.print(f"[dim]Results saved → {filepath}[/dim]")
        return str(filepath)

    def compare_strategies(self, results: dict, ticker: str, start: str, end: str) -> None:
        """Print a side-by-side comparison of multiple strategy results."""
        table = Table(
            title=f"[bold cyan]Strategy Comparison[/bold cyan]  ·  {ticker}  ·  {start} → {end}",
            box=box.DOUBLE_EDGE,
            padding=(0, 2),
        )
        table.add_column("Metric", style="dim")
        for name in results:
            table.add_column(name, justify="right", style="bold white")

        metrics = [
            ("Total Return [%]",       "Return [%]"),
            ("Buy & Hold Return [%]",  "Buy & Hold Return [%]"),
            ("Sharpe Ratio",           "Sharpe Ratio"),
            ("Max Drawdown [%]",       "Max. Drawdown [%]"),
            ("Win Rate [%]",           "Win Rate [%]"),
            ("# Trades",               "# Trades"),
        ]

        for label, key in metrics:
            row = [label]
            for stats in results.values():
                val = stats.get(key)
                if val is None:
                    row.append("N/A")
                elif "%" in label or key.endswith("[%]"):
                    color = "green" if val >= 0 else "red"
                    row.append(f"[{color}]{val:+.1f}%[/{color}]")
                elif label == "# Trades":
                    row.append(str(int(val)))
                else:
                    row.append(f"{val:.2f}")
            table.add_row(*row)

        console.print()
        console.print(table)
