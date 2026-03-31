import yaml
from pathlib import Path


class ConfigLoader:
    def load(self, path: str = "config/settings.yaml") -> dict:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path.resolve()}")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        self.validate(config)
        return config

    def validate(self, config: dict) -> None:
        required_sections = ["backtest", "paper_trading", "risk", "trend_following", "mean_reversion", "output"]
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required config section: '{section}'")

        required_risk_keys = ["position_size_pct", "stop_loss_pct", "max_open_trades"]
        for key in required_risk_keys:
            if key not in config["risk"]:
                raise ValueError(f"Missing required risk config key: '{key}'")

        if not (0 < config["risk"]["position_size_pct"] <= 1):
            raise ValueError("risk.position_size_pct must be between 0 and 1")
        if not (0 < config["risk"]["stop_loss_pct"] <= 1):
            raise ValueError("risk.stop_loss_pct must be between 0 and 1")

    def get_strategy_config(self, config: dict, name: str) -> dict:
        if name not in config:
            raise ValueError(f"Strategy config '{name}' not found in settings")
        return config[name]
