from pyghostbt.const import *
from pyghostbt.util import uuid
from pyghostbt.tool import param
from pyghostbt.tool import kline
from pyghostbt.tool import indice

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
                MODE_BACKTEST
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
            "type": "string",
            "enum": [
                CONTRACT_TYPE_THIS_WEEK,
                CONTRACT_TYPE_NEXT_WEEK,
                CONTRACT_TYPE_QUARTER,
            ],
        },
        "unit_amount": {
            "type": "integer",
            "enum": [10, 100],
        },
        "lever": {
            "type": "integer",
            "enum": [10, 20],
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
        self._p = param.Param(
            self["param"],
            db_name=self.get("db_name_param") or self.get("db_name"),
            mode=self.get("mode"),
            trade_type=self.get("trade_type"),
        )

        self._k = kline.Kline(
            symbol=self.get("symbol"),
            exchange=self.get("exchange"),
            trade_type=self.get("trade_type"),
            contract_type=self.get("contract_type"),
            db_name=self.get("db_name_kline") or self.get("db_name"),
        )

        self._i = indice.Indice()


class StrategyRuntime(Runtime):
    def __init__(self, kw):
        super().__init__(kw)


class BacktestRuntime(Runtime):
    def __init__(self, kw):
        super().__init__(kw)
        self.__setitem__("backtest_id", uuid())

        strategy_kw = kw.copy()
        strategy_kw["mode"] = MODE_ONLINE

        self._s = StrategyRuntime(strategy_kw)



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
