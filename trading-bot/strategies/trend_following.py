import pandas as pd
from backtesting.lib import crossover
from strategies.base import BaseStrategy
import indicators.technical as ind


class TrendFollowingStrategy(BaseStrategy):
    """Trend following via Moving Average crossover.

    Rules:
      BUY  when fast MA crosses above slow MA
           (and MACD histogram > 0 if use_macd_filter is True)
      SELL when fast MA crosses below slow MA
           OR stop-loss is hit (handled by backtesting.py sl= parameter)

    All parameters are set as class attributes by BacktestRunner before bt.run().
    To adjust them, edit config/settings.yaml — no code changes needed.
    """

    # Defaults — overridden by config injection in runner.py
    fast_period: int = 20
    slow_period: int = 50
    ma_type: str = "ema"
    use_macd_filter: bool = False
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9

    def init(self):
        df = pd.DataFrame({
            "Open": self.data.Open,
            "High": self.data.High,
            "Low": self.data.Low,
            "Close": self.data.Close,
            "Volume": self.data.Volume,
        })

        fast_ma = ind.moving_average(df, self.fast_period, self.ma_type)
        slow_ma = ind.moving_average(df, self.slow_period, self.ma_type)

        # self.I() registers the series with backtesting.py for plotting + NaN handling
        self.fast_ma = self.I(lambda: fast_ma.values, name=f"MA_{self.fast_period}")
        self.slow_ma = self.I(lambda: slow_ma.values, name=f"MA_{self.slow_period}")

        if self.use_macd_filter:
            macd_hist = ind.macd_histogram(df, self.macd_fast, self.macd_slow, self.macd_signal)
            self.macd_hist = self.I(lambda: macd_hist.values, name="MACD_Hist")
        else:
            self.macd_hist = None

    def next(self):
        # Already in a position — nothing to do (stop-loss is managed by backtesting.py)
        if self.position:
            return

        fast_crossed_above = crossover(self.fast_ma, self.slow_ma)
        fast_crossed_below = crossover(self.slow_ma, self.fast_ma)

        if fast_crossed_above:
            macd_ok = (self.macd_hist is None) or (self.macd_hist[-1] > 0)
            if macd_ok:
                entry_price = self.data.Close[-1]
                sl = self._stop_loss_price(entry_price)
                size = self._size_position()
                self.buy(size=size, sl=sl)

        elif fast_crossed_below:
            self.position.close()
