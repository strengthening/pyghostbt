import unittest

from pyghostbt.tool.runtime import *

config_example = {

    "mode": "online",
    "trade_type": "future",
    "symbol": "btc_usd",
    "exchange": "okex",
    "contract_type": "next_week",

    "unit_amount": 100,
    "lever": 10,
    "interval": "1min",

    "db_name": "test",
    "db_name_kline": "test",

    "param": {
        "position": 0.5,
        "max_abs_loss": 0.05,
    }
      # "order": {
      #   "symbol": "btc_usd",
      #   "exchange": "okex",
      #   "open_contract_type": "next_week",
      #   "type": "open_short",
      #   "status": "wait",
      #   "direction": "right",
      #   "position": 0.5,
      #   "strategy": "4th",
      #   "risk": "",
      #   "unit_amount": 100,
      #   "lever_rate": 20
      # },
      # "param": {
      #   "turtle_days": 20,
      #   "leak_days": 1,
      #   "leak_days_scale": 1.02,
      #   "ma_min_days": 7,
      #   "ma_max_days": 30,
      #   "atr_scale": 0.5,
      #   "heavy_profit_scale": 2.22,
      #   "light_profit_scale": 1.3,
      #   "max_loss_scale": 0.032
      # }
}


class TestToolRuntime(unittest.TestCase):
    def test_runtime_init(self):
        r = Runtime(config_example)
        print(r)

    def test_backtest_runtime(self):
        r = BacktestRuntime(config_example)
        print(r["backtest_id"])
