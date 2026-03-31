from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Position:
    ticker: str
    shares: float
    entry_price: float
    stop_loss_price: float
    entry_time: datetime = field(default_factory=datetime.now)

    @property
    def cost_basis(self) -> float:
        return self.shares * self.entry_price

    def unrealized_pnl(self, current_price: float) -> float:
        return (current_price - self.entry_price) * self.shares

    def unrealized_pnl_pct(self, current_price: float) -> float:
        return ((current_price - self.entry_price) / self.entry_price) * 100


class Portfolio:
    """Simulated portfolio for paper trading — no real money involved."""

    def __init__(self, initial_cash: float):
        self._initial_cash = initial_cash
        self._cash = initial_cash
        self._position: Optional[Position] = None
        self._realized_pnl: float = 0.0
        self._trade_log: list[dict] = []

    # ─── State ───────────────────────────────────────────────────────────────

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def position(self) -> Optional[Position]:
        return self._position

    @property
    def realized_pnl(self) -> float:
        return self._realized_pnl

    @property
    def trade_log(self) -> list[dict]:
        return self._trade_log

    def total_value(self, current_price: float = 0.0) -> float:
        if self._position:
            return self._cash + self._position.shares * current_price
        return self._cash

    # ─── Actions ─────────────────────────────────────────────────────────────

    def open_position(self, ticker: str, shares: float, price: float, stop_loss: float) -> None:
        if self._position:
            raise RuntimeError("Already in a position. Close it before opening another.")
        cost = shares * price
        if cost > self._cash:
            raise RuntimeError(f"Insufficient cash: need {cost:.2f}, have {self._cash:.2f}")
        self._cash -= cost
        self._position = Position(
            ticker=ticker,
            shares=shares,
            entry_price=price,
            stop_loss_price=stop_loss,
        )
        self._log_trade("BUY", ticker, shares, price)

    def close_position(self, price: float, reason: str = "signal") -> float:
        if not self._position:
            raise RuntimeError("No open position to close.")
        proceeds = self._position.shares * price
        pnl = proceeds - self._position.cost_basis
        self._cash += proceeds
        self._realized_pnl += pnl
        self._log_trade("SELL", self._position.ticker, self._position.shares, price, reason=reason, pnl=pnl)
        self._position = None
        return pnl

    def check_stop_loss(self, current_price: float) -> bool:
        """Return True if current price has triggered the stop-loss."""
        if not self._position:
            return False
        return current_price <= self._position.stop_loss_price

    # ─── Reporting ───────────────────────────────────────────────────────────

    def summary(self, current_price: float = 0.0) -> dict:
        unrealized = self._position.unrealized_pnl(current_price) if self._position else 0.0
        unrealized_pct = self._position.unrealized_pnl_pct(current_price) if self._position else 0.0
        total_val = self.total_value(current_price)
        total_return_pct = ((total_val - self._initial_cash) / self._initial_cash) * 100
        trades = [t for t in self._trade_log if t["side"] == "SELL"]
        wins = [t for t in trades if t.get("pnl", 0) > 0]
        win_rate = (len(wins) / len(trades) * 100) if trades else 0.0

        return {
            "initial_cash": self._initial_cash,
            "cash": self._cash,
            "portfolio_value": total_val,
            "total_return_pct": total_return_pct,
            "realized_pnl": self._realized_pnl,
            "unrealized_pnl": unrealized,
            "unrealized_pnl_pct": unrealized_pct,
            "open_position": bool(self._position),
            "position_ticker": self._position.ticker if self._position else None,
            "position_shares": self._position.shares if self._position else 0,
            "position_entry": self._position.entry_price if self._position else 0,
            "num_trades": len(trades),
            "win_rate": win_rate,
        }

    def _log_trade(self, side: str, ticker: str, shares: float, price: float, reason: str = "", pnl: float = 0.0):
        self._trade_log.append({
            "time": datetime.now().isoformat(),
            "side": side,
            "ticker": ticker,
            "shares": shares,
            "price": price,
            "reason": reason,
            "pnl": pnl,
        })
