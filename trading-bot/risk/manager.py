class RiskManager:
    def __init__(self, config: dict):
        self._position_size_pct = config["position_size_pct"]
        self._stop_loss_pct = config["stop_loss_pct"]

    def position_size(self, equity: float, price: float) -> float:
        """Return the fraction of equity to allocate (0.0–1.0).

        backtesting.py's self.buy(size=...) accepts a fraction when between 0 and 1,
        or a share count when >= 1. We return a fraction here.
        """
        if price <= 0:
            return 0.0
        allocation = equity * self._position_size_pct
        shares = allocation / price
        # Return as a fraction of current equity
        fraction = (shares * price) / equity
        return round(min(fraction, 1.0), 4)

    def stop_loss_price(self, entry_price: float, direction: str = "long") -> float:
        """Return the absolute stop-loss price.

        direction: 'long'  → stop below entry
                   'short' → stop above entry (not used yet, reserved for future)
        """
        if direction == "long":
            return round(entry_price * (1 - self._stop_loss_pct), 4)
        elif direction == "short":
            return round(entry_price * (1 + self._stop_loss_pct), 4)
        else:
            raise ValueError(f"Unknown direction '{direction}'. Use 'long' or 'short'.")
