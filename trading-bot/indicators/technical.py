"""
Pure indicator functions — each takes a DataFrame and returns a Series or DataFrame.
Nothing is mutated in-place. All use pandas-ta under the hood.
"""

import pandas as pd
import pandas_ta as ta


def moving_average(df: pd.DataFrame, period: int, ma_type: str = "ema") -> pd.Series:
    """Return EMA or SMA of Close prices."""
    if ma_type.lower() == "ema":
        result = ta.ema(df["Close"], length=period)
    elif ma_type.lower() == "sma":
        result = ta.sma(df["Close"], length=period)
    else:
        raise ValueError(f"Unknown ma_type '{ma_type}'. Use 'ema' or 'sma'.")
    return result


def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Relative Strength Index of Close prices."""
    return ta.rsi(df["Close"], length=period)


def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD line, signal line, and histogram.

    Returns a DataFrame with columns:
        MACD_{fast}_{slow}_{signal}
        MACDs_{fast}_{slow}_{signal}   (signal line)
        MACDh_{fast}_{slow}_{signal}   (histogram)
    """
    result = ta.macd(df["Close"], fast=fast, slow=slow, signal=signal)
    return result


def bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands — upper, middle (SMA), lower.

    Returns a DataFrame with columns:
        BBU_{period}_{std}   (upper band)
        BBM_{period}_{std}   (middle band / SMA)
        BBL_{period}_{std}   (lower band)
    """
    result = ta.bbands(df["Close"], length=period, std=std)
    return result


def macd_histogram(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    """Convenience wrapper — returns just the MACD histogram Series."""
    result = macd(df, fast, slow, signal)
    hist_col = [c for c in result.columns if c.startswith("MACDh")]
    if not hist_col:
        raise ValueError("MACD histogram column not found in pandas-ta output")
    return result[hist_col[0]]


def bb_upper(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.Series:
    """Convenience wrapper — returns just the upper Bollinger Band."""
    result = bollinger_bands(df, period, std)
    col = [c for c in result.columns if c.startswith("BBU")]
    return result[col[0]]


def bb_lower(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.Series:
    """Convenience wrapper — returns just the lower Bollinger Band."""
    result = bollinger_bands(df, period, std)
    col = [c for c in result.columns if c.startswith("BBL")]
    return result[col[0]]
