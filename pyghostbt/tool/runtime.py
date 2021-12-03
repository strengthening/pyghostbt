from pyghostbt.tool.kline import Kline
from pyghostbt.tool.factor import Factor
from pyghostbt.tool.signal import Signal
from pyghostbt.util import uuid
from pyghostbt.const import *
from jsonschema import validate

runtime_input = {
    "type": "object",
    "required": ["mode", "trade_type", "symbol", "exchange", "db_name"],
    "properties": {
        "mode": {
            "type": "string",
            "enum": [
                MODE_ONLINE,
                MODE_OFFLINE,
                MODE_BACKTEST,
                MODE_STRATEGY,
            ],
        },
        "trade_type": {
            "type": "string",
            "enum": [
                TRADE_TYPE_FUTURE,
                TRADE_TYPE_SWAP,
                TRADE_TYPE_MARGIN,
                TRADE_TYPE_SPOT,
            ],
        },
        "symbol": {
            "type": "string",
        },
        "exchange": {
            "type": "string",
        },
        "db_name": {
            "type": "string",
        },
        "contract_type": {
            "type": ["null", "string"],
            "enum": [
                None,
                CONTRACT_TYPE_THIS_WEEK,
                CONTRACT_TYPE_NEXT_WEEK,
                CONTRACT_TYPE_QUARTER,
            ],
        },
        "unit_amount": {
            "type": "number",
            "minimum": 0,
        },
        "lever": {
            "type": "integer",
            "enum": [1, 10, 20],
        },
        "interval": {
            "type": "string",
            "enum": [
                KLINE_INTERVAL_1MIN,
                KLINE_INTERVAL_15MIN,
                KLINE_INTERVAL_1HOUR,
                KLINE_INTERVAL_4HOUR,
                KLINE_INTERVAL_1DAY,
                KLINE_INTERVAL_1WEEK,
            ],
        }
    }
}


class Runtime(dict):
    def __init__(self, kw):
        super().__init__(kw)
        validate(instance=self, schema=runtime_input)
        if not self.get("backtest_id"):
            if self.get("mode") == MODE_BACKTEST:
                self.__setitem__("backtest_id", uuid())

        self._kline = Kline(
            trade_type=self.get("trade_type"),
            symbol=self.get("symbol"),
            exchange=self.get("exchange"),
            contract_type=self.get("contract_type"),
            db_name=self.get("db_name_kline") or self.get("db_name"),
        )

        self._factor = Factor(
            trade_type=self.get("trade_type"),
            symbol=self.get("symbol"),
            contract_type=self.get("contract_type"),
            db_name=self.get("db_name_kline") or self.get("db_name"),
        )

        self._signal = Signal(
            trade_type=self.get("trade_type"),
            symbol=self.get("symbol"),
            exchange=self.get("exchange"),
            contract_type=self.get("contract_type"),
            db_name=self.get("db_name_kline") or self.get("db_name"),
        )

# class StrategyRuntime(Runtime):
#     def __init__(self, kw):
#         super().__init__(kw)
#
#
# class BacktestRuntime(Runtime):
#     def __init__(self, kw):
#         super().__init__(kw)
#
#         strategy_kw = kw.copy()
#         self._s = StrategyRuntime(strategy_kw)


# if __name__ == "__main__":
#     r = Runtime({"a":1, "param":{}})
#     print(r["a"])
#     print(r["param"])
#     print(r["test"])
#     print(r.items())
#
#     for (k, v) in r.items():
#         print(k)
#         print(v)
