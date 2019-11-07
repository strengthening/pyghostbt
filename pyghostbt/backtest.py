from jsonschema import validate
from pyghostbt.util import uuid
from pyghostbt.strategy import Strategy
from pyghostbt.const import *
from pyanalysis.mysql import Conn

instance_param = {
    "type": "object",
    "required": [
        "id", "symbol", "exchange", "strategy", "status", "interval", "start_timestamp", "start_datetime",
        "finish_timestamp", "finish_datetime", "total_asset", "sub_freeze_asset", "param_position", "param_max_abs_loss",
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
        "contract_type": {
            "type": "string",
            "enum": [
                CONTRACT_TYPE_THIS_WEEK,
                CONTRACT_TYPE_NEXT_WEEK,
                CONTRACT_TYPE_QUARTER,
            ],
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
            "type": "number",
            "minimum": 0,
        },
        "sub_freeze_asset": {
            "type": "number"
        },
        "param_position": {
            "type": "number"
        },
        "param_max_abs_loss": {
            "type": "number",
            "minimum": -0.5,
            "maximum": 0.5,
        },
    }
}


class Backtest(Strategy):
    def __init__(self, kw):
        super().__init__(kw)
        if not self.get("backtest_id"):
            self.__setitem__("backtest_id", uuid())

        # self._slippage = 0.01  # 滑点百分比
        # self._fee = -0.0005  # 手续费比例

    @staticmethod
    def __compare_candle_with_instance(candle, instance):
        ask_side = instance["order"]["type"] == 1 or instance["order"]["type"] == 4
        order_price = instance["order"]["price"]
        if instance["order"]["place_type"] == "t_taker":
            column_name = "high" if ask_side else "low"
            candle_price = candle[column_name]
            match = candle_price > order_price if ask_side else candle_price < order_price
            if match:
                instance["order"]["place_timestamp"] = candle["timestamp"]
                instance["order"]["place_datetime"] = candle["date"]
                instance["order"]["deal_timestamp"] = candle["timestamp"]
                instance["order"]["deal_datetime"] = candle["date"]
                instance["order"]["due_timestamp"] = candle["due_timestamp"]
                instance["order"]["due_datetime"] = candle["due_date"]
                return instance
        elif instance["order"]["place_type"] == "b_taker":
            column_name = "low" if ask_side else "high"
            candle_price = candle[column_name]
            match = candle_price < order_price if ask_side else candle_price > order_price
            if match:
                instance["order"]["place_timestamp"] = candle["timestamp"]
                instance["order"]["place_datetime"] = candle["date"]
                instance["order"]["deal_timestamp"] = candle["timestamp"]
                instance["order"]["deal_datetime"] = candle["date"]
                instance["order"]["due_timestamp"] = candle["due_timestamp"]
                instance["order"]["due_datetime"] = candle["due_date"]
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

    def save(self):
        self.check_instance(self)
        conn = Conn(self["db_name"])
        one = conn.query_one(
            "SELECT id FROM {trade_type}_instance_{mode} WHERE id = ?".format(**self),
            (self["id"],),
        )
        if one:
            conn.execute(
                "UPDATE {trade_type}_instance_{mode} SET symbol = ?, exchange = ?, contract_type = ?, "
                "strategy = ?, unit_amount = ?, lever = ?, status = ?, `interval` = ?, "
                "start_timestamp = ?, start_datetime = ?, finish_timestamp = ?, finish_datetime = ?, "
                "total_asset = ?, sub_freeze_asset = ?, param_position = ?, param_max_abs_loss = ? "
                "WHERE id = ?".format(**self),
                (
                    self["symbol"], self["exchange"], self["contract_type"],
                    self["strategy"], self["unit_amount"], self["lever"], self["status"],
                    self["interval"], self["start_timestamp"], self["start_datetime"],
                    self["finish_timestamp"], self["finish_datetime"], self["total_asset"],
                    self["sub_freeze_asset"], self["param_position"], self["param_max_abs_loss"],
                    self["id"],
                ),
            )

            self["order"].deal()
            self["order"].save(check=True)
            # conn.insert(
            #     "INSERT INTO {trade_type}_order_{mode} (instance_id, sequence, place_type, type, price,"
            #     " amount, avg_price, deal_amount, status, lever, fee, symbol, exchange, contract_type,"
            #     " place_timestamp, place_datetime, deal_timestamp, deal_datetime, due_timestamp, due_datetime,"
            #     " swap_timestamp, swap_datetime, cancel_timestamp, cancel_datetime) VALUES"
            #     " (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(**self),
            #     (
            #         order["instance_id"], order["sequence"], order["place_type"], order["type"], order["price"],
            #         order["amount"], order["avg_price"], order["deal_amount"], order["status"], order["lever"],
            #         order["fee"], order["symbol"], order["exchange"], order["contract_type"], order["place_timestamp"],
            #         order["place_datetime"], order["deal_timestamp"], order["deal_datetime"], order["due_timestamp"],
            #         order["due_datetime"], order["swap_timestamp"], order["swap_datetime"],
            #         order["cancel_timestamp"], order["cancel_datetime"],
            #     )
            # )
        else:
            raise RuntimeError("I think can not insert in this place. ")
        # conn.insert(
        #     "INSERT INTO {trade_type}_instance_{mode} (symbol, exchange, contract_type, strategy, unit_amount,"
        #     "lever, status, `interval`, start_timestamp, start_datetime, finish_timestamp, finish_datetime,"
        #     "total_asset, sub_freeze_asset, param_position, param_max_abs_loss)"
        #     " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(**self),
        #     (
        #         self["symbol"], self["exchange"], self["contract_type"],
        #         self["strategy"], self["unit_amount"], self["lever"], self["status"],
        #         self["interval"], self["start_timestamp"], self["start_datetime"],
        #         self["finish_timestamp"], self["finish_datetime"], self["total_asset"],
        #         self["sub_freeze_asset"], self["param_position"], self["param_max_abs_loss"],
        #     ),
        # )

    # 判断是否触发，将结果返回，并将触发的instance信息合并到当前的对象上。
    def back_test_wait_open(self, timestamp: int) -> bool:
        pass

    def back_test_opening(self, timestamp: int) -> bool:
        pass

    def back_test_wait_liquidate(self, timestamp: int) -> bool:
        pass

    def back_test_liquidating(self, timestamp: int) -> bool:
        pass
