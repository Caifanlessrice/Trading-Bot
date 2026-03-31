import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path


class DataFetcher:
    def __init__(self, cache_dir: str = None):
        self._cache_dir = Path(cache_dir) if cache_dir else None

    def fetch(self, ticker: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        """Download OHLCV data for backtesting. Returns a clean DataFrame."""
        cache_path = self._cache_path(ticker, start, end, interval)
        if cache_path and cache_path.exists():
            df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            return df

        df = yf.download(ticker, start=start, end=end, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            raise ValueError(f"No data returned for {ticker} ({start} → {end})")

        df = self._clean(df)
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(cache_path)

        return df

    def fetch_latest(self, ticker: str, lookback_days: int = 200, interval: str = "1d") -> pd.DataFrame:
        """Fetch recent bars for paper trading indicator warmup."""
        end = datetime.today().strftime("%Y-%m-%d")
        start = (datetime.today() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        return self.fetch(ticker, start, end, interval)

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # Flatten MultiIndex columns if present (yfinance sometimes returns them)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Standardise column names
        df.columns = [c.strip().title() for c in df.columns]

        required = ["Open", "High", "Low", "Close", "Volume"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Downloaded data missing columns: {missing}")

        df = df[required].copy()
        df.dropna(subset=["Close"], inplace=True)
        df.index = pd.to_datetime(df.index)
        return df

    def _cache_path(self, ticker, start, end, interval) -> Path | None:
        if not self._cache_dir:
            return None
        filename = f"{ticker}_{start}_{end}_{interval}.csv".replace(" ", "_")
        return self._cache_dir / filename
