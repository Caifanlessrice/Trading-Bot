"""
Paper trading engine.

On each tick it:
  1. Fetches the latest price bar from yfinance
  2. Appends it to the running history DataFrame
  3. Re-computes indicators
  4. Evaluates entry / exit signals (same logic as the backtesting strategies)
  5. Simulates fills via the Portfolio
  6. Prints an updated summary
"""

import time
import schedule
import pandas as pd
from datetime import datetime

from data.fetcher import DataFetcher
from paper_trading.portfolio import Portfolio
from paper_trading.reporter import PaperReporter
from risk.manager import RiskManager
import indicators.technical as ind


class PaperEngine:
    def __init__(self, config: dict, ticker: str, strategy_name: str):
        self._config = config
        self._ticker = ticker
        self._strategy_name = strategy_name
        self._pt_cfg = config["paper_trading"]
        self._risk = RiskManager(config["risk"])

        initial_cash = self._pt_cfg["initial_cash"]
        self._portfolio = Portfolio(initial_cash)
        self._reporter = PaperReporter()
        self._fetcher = DataFetcher()
        self._history: pd.DataFrame = pd.DataFrame()

    def start(self) -> None:
        """Begin paper trading. Runs until the user presses Ctrl+C."""
        print(f"\n[Paper Trading] {self._ticker} · Strategy: {self._strategy_name}")
        print(f"Checking every {self._pt_cfg['check_interval_minutes']} minute(s). Press Ctrl+C to stop.\n")

        # Load warmup history so indicators have enough bars from the start
        lookback = self._pt_cfg.get("lookback_days", 200)
        interval = self._pt_cfg.get("data_interval", "1d")
        self._history = self._fetcher.fetch_latest(self._ticker, lookback_days=lookback, interval=interval)

        # Run immediately on start, then on schedule
        self._tick()
        interval_min = self._pt_cfg["check_interval_minutes"]
        schedule.every(interval_min).minutes.do(self._tick)

        try:
            while True:
                schedule.run_pending()
                time.sleep(30)
        except KeyboardInterrupt:
            print("\n[Paper Trading] Stopped by user.")
            self._reporter.print_final(self._portfolio, self._ticker)

    def _tick(self) -> None:
        """Single evaluation cycle."""
        try:
            latest = self._fetcher.fetch_latest(self._ticker, lookback_days=1, interval=self._pt_cfg["data_interval"])
            if latest.empty:
                return
            # Append the latest bar (avoid duplicates)
            self._history = pd.concat([self._history, latest]).drop_duplicates().sort_index()

            price = float(self._history["Close"].iloc[-1])
            signal = self._compute_signal()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")

            # Check stop-loss first
            if self._portfolio.check_stop_loss(price):
                pnl = self._portfolio.close_position(price, reason="stop-loss")
                print(f"[{now}] STOP-LOSS triggered at {price:.2f} · P&L: {pnl:+.2f}")

            elif signal == "buy" and not self._portfolio.position:
                equity = self._portfolio.total_value(price)
                fraction = self._risk.position_size(equity, price)
                shares = (equity * fraction) / price
                sl = self._risk.stop_loss_price(price, "long")
                self._portfolio.open_position(self._ticker, shares, price, sl)
                print(f"[{now}] BUY  {shares:.4f} shares @ {price:.2f}  SL={sl:.2f}")

            elif signal == "sell" and self._portfolio.position:
                pnl = self._portfolio.close_position(price, reason="signal")
                print(f"[{now}] SELL @ {price:.2f}  P&L: {pnl:+.2f}")

            else:
                print(f"[{now}] HOLD · price={price:.2f} · signal={signal}")

            self._reporter.print_summary(self._portfolio, price, self._ticker)

        except Exception as e:
            print(f"[tick error] {e}")

    def _compute_signal(self) -> str:
        """Return 'buy', 'sell', or 'hold' based on the chosen strategy."""
        if self._strategy_name == "trend":
            return self._trend_signal()
        elif self._strategy_name == "mean":
            return self._mean_signal()
        return "hold"

    # ─── Trend following signal ───────────────────────────────────────────────

    def _trend_signal(self) -> str:
        cfg = self._config["trend_following"]
        fast = ind.moving_average(self._history, cfg["fast_period"], cfg["ma_type"])
        slow = ind.moving_average(self._history, cfg["slow_period"], cfg["ma_type"])

        if fast.isna().iloc[-1] or slow.isna().iloc[-1]:
            return "hold"

        fast_prev, fast_curr = fast.iloc[-2], fast.iloc[-1]
        slow_prev, slow_curr = slow.iloc[-2], slow.iloc[-1]

        crossed_up   = fast_prev <= slow_prev and fast_curr > slow_curr
        crossed_down = fast_prev >= slow_prev and fast_curr < slow_curr

        if crossed_up:
            if cfg.get("use_macd_filter", False):
                hist = ind.macd_histogram(self._history, cfg["macd_fast"], cfg["macd_slow"], cfg["macd_signal"])
                if hist.iloc[-1] <= 0:
                    return "hold"
            return "buy"
        elif crossed_down:
            return "sell"
        return "hold"

    # ─── Mean reversion signal ────────────────────────────────────────────────

    def _mean_signal(self) -> str:
        cfg = self._config["mean_reversion"]
        rsi_series = ind.rsi(self._history, cfg["rsi_period"])
        if rsi_series.isna().iloc[-1]:
            return "hold"

        rsi_val = rsi_series.iloc[-1]
        price = float(self._history["Close"].iloc[-1])

        if rsi_val < cfg["rsi_oversold"]:
            if cfg.get("use_bb_confirm", True):
                lower = ind.bb_lower(self._history, cfg["bb_period"], cfg["bb_std"])
                if lower.isna().iloc[-1] or price > float(lower.iloc[-1]):
                    return "hold"
            return "buy"

        elif rsi_val > cfg["rsi_overbought"]:
            if cfg.get("use_bb_confirm", True):
                upper = ind.bb_upper(self._history, cfg["bb_period"], cfg["bb_std"])
                if upper.isna().iloc[-1] or price < float(upper.iloc[-1]):
                    return "hold"
            return "sell"

        return "hold"
