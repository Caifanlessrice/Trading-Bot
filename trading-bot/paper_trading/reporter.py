from rich.console import Console
from rich.table import Table
from rich import box

from paper_trading.portfolio import Portfolio

console = Console()


class PaperReporter:
    def print_summary(self, portfolio: Portfolio, current_price: float, ticker: str) -> None:
        """Print a live performance snapshot."""
        s = portfolio.summary(current_price)

        table = Table(
            title=f"[bold cyan]Paper Trading — {ticker}[/bold cyan]",
            box=box.SIMPLE_HEAD,
            show_header=False,
            padding=(0, 2),
        )
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right", style="bold white")

        def _money(val):
            color = "green" if val >= 0 else "red"
            return f"[{color}]${val:,.2f}[/{color}]"

        def _pct(val):
            color = "green" if val >= 0 else "red"
            return f"[{color}]{val:+.2f}%[/{color}]"

        table.add_row("Portfolio Value",   _money(s["portfolio_value"]))
        table.add_row("Cash",              _money(s["cash"]))
        table.add_row("Total Return",      _pct(s["total_return_pct"]))
        table.add_row("Realized P&L",      _money(s["realized_pnl"]))
        table.add_row("Unrealized P&L",    _money(s["unrealized_pnl"]) + f"  ({_pct(s['unrealized_pnl_pct'])})" if s["open_position"] else "[dim]No open position[/dim]")
        table.add_row("# Closed Trades",   str(s["num_trades"]))
        table.add_row("Win Rate",          f"{s['win_rate']:.1f}%" if s["num_trades"] > 0 else "—")

        if s["open_position"]:
            table.add_row("Open Position", f"{s['position_ticker']}  ×{s['position_shares']:.4f} @ ${s['position_entry']:.2f}")

        console.print(table)

    def print_final(self, portfolio: Portfolio, ticker: str) -> None:
        """Print the final performance sheet when the session ends."""
        console.print("\n[bold]─── Final Session Summary ───[/bold]")
        # Use last known close (0 if no open position, reported separately)
        self.print_summary(portfolio, current_price=0.0, ticker=ticker)

        if portfolio.trade_log:
            console.print("\n[bold]Trade Log:[/bold]")
            for t in portfolio.trade_log:
                pnl_str = f"  P&L: {t['pnl']:+.2f}" if t["side"] == "SELL" else ""
                console.print(f"  {t['time']}  {t['side']:4s}  {t['shares']:.4f} × ${t['price']:.2f}{pnl_str}")
