import pandas as pd
from backtesting import Backtest
from strategies.trend_following import TrendFollowingStrategy
from strategies.mean_reversion import MeanReversionStrategy

STRATEGY_MAP = {
    "trend": TrendFollowingStrategy,
    "mean": MeanReversionStrategy,
}


class BacktestRunner:
    def __init__(self, config: dict):
        self._config = config

    def run(self, strategy_name: str, data: pd.DataFrame):
        """Run a single backtest. Returns a backtesting.py Stats object."""
        strategy_class = self._get_strategy_class(strategy_name)
        self._inject_config(strategy_class, strategy_name)

        bt_cfg = self._config["backtest"]
        bt = Backtest(
            data,
            strategy_class,
            cash=bt_cfg["initial_cash"],
            commission=bt_cfg["commission"],
            exclusive_orders=True,
        )
        return bt.run()

    def optimize(self, strategy_name: str, data: pd.DataFrame, param_grid: dict):
        """Run parameter optimisation. Returns a sorted DataFrame of results."""
        strategy_class = self._get_strategy_class(strategy_name)
        self._inject_config(strategy_class, strategy_name)

        bt_cfg = self._config["backtest"]
        bt = Backtest(
            data,
            strategy_class,
            cash=bt_cfg["initial_cash"],
            commission=bt_cfg["commission"],
            exclusive_orders=True,
        )
        stats, heatmap = bt.optimize(
            **param_grid,
            maximize="Sharpe Ratio",
            return_heatmap=True,
        )
        return stats, heatmap

    def _get_strategy_class(self, name: str):
        if name not in STRATEGY_MAP:
            raise ValueError(f"Unknown strategy '{name}'. Choose from: {list(STRATEGY_MAP.keys())}")
        return STRATEGY_MAP[name]

    def _inject_config(self, strategy_class, strategy_name: str):
        """Set config values as class attributes so backtesting.py picks them up."""
        strategy_class.config = self._config

        cfg_key = "trend_following" if strategy_name == "trend" else "mean_reversion"
        strategy_cfg = self._config.get(cfg_key, {})

        for key, value in strategy_cfg.items():
            setattr(strategy_class, key, value)
