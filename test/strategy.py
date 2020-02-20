import unittest
import json

from pyanalysis.mysql import Conn
from pyanalysis.moment import moment as m
from pyghostbt.strategy import Strategy
from pyghostbt.tool.order import *
from pyghostbt.tool.runtime import Runtime
from pyghostbt.const import *
from dateutil import tz

strategy_1st_config = {
    "mode": "backtest",
    "symbol": "btc_usd",
    "exchange": "okex",
    "contract_type": "quarter",
    "trade_type": "future",
    "unit_amount": 100,
    "lever": 10,
    "interval": "1min",

    "db_name": "test",
    "db_name_kline": "ghost-etl",
    "timezone": "Asia/Shanghai",
    "param": {
        "position": 0.5,
        "max_abs_loss": 0.05,
    },
    "order": {}
}


class Strategy1st(Strategy):
    def __init__(self, kw):
        super().__init__(kw)

    def get_wait_open(self, timestamp):
        moment = m.get(timestamp)
        the_last_day = moment.to(self["timezone"] or "Asia/Shanghai").floor("day")
        the_start_day = the_last_day.shift(days=-20)
        results = self._kline.query(
            the_start_day.millisecond_timestamp,
            the_last_day.millisecond_timestamp,
            KLINE_INTERVAL_1DAY,
            standard=True,
        )

        self["a"].init_account(10)

        price = max([result["high"] for result in results])
        asset = self._a.get_last_asset(timestamp)["total_account_asset"]
        amount = int(asset * price * self["param"]["position"] / 100000000 / self["unit_amount"])

        return [FutureOrder(
            trade_type=self["trade_type"],
            place_type=ORDER_PLACE_TYPE_T_TAKER,
            db_name=self["db_name"],
            mode=self["mode"],
            symbol=self["symbol"],
            exchange=self["exchange"],
            contract_type=self["contract_type"],
            instance_id=self["instance_id"],
            sequence=0,
            backtest_id=self["backtest_id"],
            price=price,
            amount=amount,
            lever=self["lever"],
        )]

    def get_opening(self, timestamp):
        pass

    def get_wait_liquidate(self, timestamp):
        pass

    def get_liquidating(self, timestamp):
        pass


class TestStrategy(unittest.TestCase):
    def test_turtles(self):
        rt = Runtime(strategy_1st_config)
        print(json.dumps(rt))
        # s_1st = Strategy1st(strategy_1st_config)
        # s_1st.get_wait_open(1572246247000)

    # def test_tool_kline(self):
    #     pass
