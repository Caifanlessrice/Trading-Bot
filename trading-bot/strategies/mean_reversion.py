import pandas as pd
from strategies.base import BaseStrategy
import indicators.technical as ind


class MeanReversionStrategy(BaseStrategy):
    """Mean reversion via RSI with optional Bollinger Band confirmation.

    Rules:
      BUY  when RSI < rsi_oversold
           (and price <= lower Bollinger Band if use_bb_confirm is True)
      SELL when RSI > rsi_overbought
           (and price >= upper Bollinger Band if use_bb_confirm is True)
           OR stop-loss is hit (handled by backtesting.py sl= parameter)

    All parameters are set as class attributes by BacktestRunner before bt.run().
    To adjust them, edit config/settings.yaml — no code changes needed.
    """

    # Defaults — overridden by config injection in runner.py
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    use_bb_confirm: bool = True
    bb_period: int = 20
    bb_std: float = 2.0

    def init(self):
        df = pd.DataFrame({
            "Open": self.data.Open,
            "High": self.data.High,
            "Low": self.data.Low,
            "Close": self.data.Close,
            "Volume": self.data.Volume,
        })

        rsi_series = ind.rsi(df, self.rsi_period)
        self.rsi = self.I(lambda: rsi_series.values, name=f"RSI_{self.rsi_period}")

        if self.use_bb_confirm:
            upper = ind.bb_upper(df, self.bb_period, self.bb_std)
            lower = ind.bb_lower(df, self.bb_period, self.bb_std)
            self.bb_upper = self.I(lambda: upper.values, name="BB_Upper")
            self.bb_lower = self.I(lambda: lower.values, name="BB_Lower")
        else:
            self.bb_upper = None
            self.bb_lower = None

    def next(self):
        rsi_val = self.rsi[-1]
        price = self.data.Close[-1]

        if not self.position:
            # Entry: RSI oversold (+ below lower BB if confirm enabled)
            bb_buy_ok = (self.bb_lower is None) or (price <= self.bb_lower[-1])
            if rsi_val < self.rsi_oversold and bb_buy_ok:
                entry_price = price
                sl = self._stop_loss_price(entry_price)
                size = self._size_position()
                self.buy(size=size, sl=sl)
        else:
            # Exit: RSI overbought (+ above upper BB if confirm enabled)
            bb_sell_ok = (self.bb_upper is None) or (price >= self.bb_upper[-1])
            if rsi_val > self.rsi_overbought and bb_sell_ok:
                self.position.close()
