from jsonschema import validate
from pyghostbt.util import uuid
from pyghostbt.strategy import Strategy
from pyghostbt.const import *
from pyanalysis.mysql import Conn


instance_param = {
    "type": "object",
    "required": [
        "id", "symbol", "exchange", "strategy", "status", "interval", "start_timestamp", "start_datetime",
        "finish_timestamp", "finish_datetime", "total_asset", "freeze_asset", "param_position", "param_max_abs_loss",
    ],
    "properties": {
        "id": {
            "type": "integer",
        },
        "symbol": {
            "type": "string",
        },
        "exchange": {
            "type": "string",
        },
        "strategy": {
            "type": "string",
        },
        "status": {
            "type": "integer",
            "enum": [
                INSTANCE_STATUS_WAIT_OPEN,
                INSTANCE_STATUS_OPENING,
                INSTANCE_STATUS_WAIT_LIQUIDATE,
                INSTANCE_STATUS_LIQUIDATING,
                INSTANCE_STATUS_FINISHED,
                INSTANCE_STATUS_ERROR,
            ],
        },
        "contract_type": {
            "type": "string",
            "enum": [
                CONTRACT_TYPE_THIS_WEEK,
                CONTRACT_TYPE_NEXT_WEEK,
                CONTRACT_TYPE_QUARTER,
            ],
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
        },
        "unit_amount": {
            "type": "integer",
            "enum": [10, 100],
        },
        "lever": {
            "type": "integer",
            "enum": [10, 20],
        },
        "start_timestamp": {
            "type": "integer",
            "minimum": 1000000000000,
            "maximum": 3000000000000,
        },
        "start_datetime": {
            "type": "string"
        },
        "finish_timestamp": {
            "type": "integer",
            "minimum": 1000000000000,
            "maximum": 3000000000000,
        },
        "finish_datetime": {
            "type": "string"
        },
        "total_asset": {
            "type": "number"
        },
        "freeze_asset": {
            "type": "number"
        },
        "param_position": {
            "type": "number"
        },
        "param_max_abs_loss": {
            "type": "number"
        },
    }
}


class Backtest(Strategy):
    def __init__(self, kw):
        super().__init__(kw)
        if not self.get("backtest_id"):
            self.__setitem__("backtest_id", uuid())

    @staticmethod
    def __compare_candle_with_instance(candle, instance):
        ask_side = instance["order"]["type"] == 1 or instance["order"]["type"] == 4
        order_price = instance["order"]["price"]
        if instance["order"]["place_type"] == "t_taker":
            column_name = "high" if ask_side else "low"
            candle_price = candle[column_name]
            match = candle_price > order_price if ask_side else candle_price < order_price
            if match:
                return instance
        elif instance["order"]["place_type"] == "b_taker":
            column_name = "low" if ask_side else "high"
            candle_price = candle[column_name]
            match = candle_price < order_price if ask_side else candle_price > order_price
            if match:
                return instance
        else:
            raise RuntimeError("do not support the other place_type")
        return None

    def _back_test_by_min_kline(self, start_timestamp, finish_timestamp, instances=None, standard=True):
        candles = self._k.range_query(
            start_timestamp,
            finish_timestamp,
            KLINE_INTERVAL_1MIN,
            standard=standard
        )
        # instance 触发了
        for candle in candles:
            for instance in instances:
                if self.__compare_candle_with_instance(candle, instance):
                    return instance
        # instance 没触发
        return None

    def _back_test_by_day_kline(self, start_timestamp, finish_timestamp, instances=None, standard=True):
        candles = self._k.raw_query(
            start_timestamp,
            finish_timestamp,
            KLINE_INTERVAL_1DAY,
            standard=standard
        )

        for candle in candles:
            for instance in instances:
                if self.__compare_candle_with_instance(candle, instance):
                    return instance
        # instance 没触发
        return None

    def back_test_wait_open(self, instances):
        pass

    @staticmethod
    def check_wait_open_instance(instance):
        validate(instance=instance, schema=instance_param)

    def save(self, instance):
        conn = Conn(self["db_name"])
        one = conn.query_one(
            "SELECT id FROM {trade_type}_instance_{mode} WHERE id = ?".format(**self),
            (self["id"], ),
        )

        if one:
            conn.execute(
                "UPDATE {trade_type}_instance_{mode} SET a = ?, b = ? WHERE id = ?".format(**self),
                (),
            )

        conn.insert(
            "INSERT INTO {trade_type}_instance_{mode} () VALUES ()",
            (),
        )

    def back_test_opening(self, instances):
        pass

    def back_test_wait_liquidate(self, timestamp):
        pass

    def back_test_liquidating(self, timestamp):
        pass
