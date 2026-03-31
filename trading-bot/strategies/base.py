from backtesting import Strategy
from risk.manager import RiskManager


class BaseStrategy(Strategy):
    """Shared foundation for all strategies.

    Subclasses inherit position sizing and stop-loss helpers.
    Config is injected as class attributes by BacktestRunner before bt.run().
    """

    # Injected by BacktestRunner — holds the full config dict
    config: dict = {}

    def _risk_manager(self) -> RiskManager:
        return RiskManager(self.config.get("risk", {}))

    def _size_position(self) -> float:
        """Return fraction of equity to allocate to this trade."""
        rm = self._risk_manager()
        return rm.position_size(equity=self.equity, price=self.data.Close[-1])

    def _stop_loss_price(self, entry_price: float) -> float:
        """Return absolute stop-loss price for a long entry."""
        rm = self._risk_manager()
        return rm.stop_loss_price(entry_price, direction="long")

    def init(self):
        raise NotImplementedError("Subclasses must implement init()")

    def next(self):
        raise NotImplementedError("Subclasses must implement next()")
