from jsonschema import validate
from pyghostbt.strategy import Strategy
from pyghostbt.const import *
from pyanalysis.mysql import Conn

instance_param = {
    "type": "object",
    "required": [
        "id", "symbol", "exchange", "strategy", "status", "interval", "start_timestamp", "start_datetime",
        "finish_timestamp", "finish_datetime", "total_asset", "sub_freeze_asset", "param_position",
        "param_max_abs_loss",
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
                INSTANCE_STATUS_WAITING,
                INSTANCE_STATUS_OPENING,
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

        # self._slippage = 0.01  # 滑点百分比
        # self._fee = -0.0005  # 手续费比例

    @staticmethod
    def __compare_candle_with_instance(candle, instance):
        order_price = instance["order"]["price"]
        if instance["order"]["place_type"] == ORDER_PLACE_TYPE_T_TAKER:
            candle_price = candle["high"]
            if candle_price > order_price:
                instance["order"]["place_timestamp"] = candle["timestamp"]
                instance["order"]["place_datetime"] = candle["date"]
                instance["order"]["deal_timestamp"] = candle["timestamp"]
                instance["order"]["deal_datetime"] = candle["date"]
                instance["order"]["due_timestamp"] = candle["due_timestamp"]
                instance["order"]["due_datetime"] = candle["due_date"]
                return instance
        elif instance["order"]["place_type"] == ORDER_PLACE_TYPE_B_TAKER:
            candle_price = candle["low"]
            if candle_price < order_price:
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

    # todo 同一个timestamp中不同的due_timestamp kline
    def __compare_candles_with_instances(self, candles, instances):
        print(self)
        return {}

    def _back_test_swap_by_min_kline(self, swap_timestamp, due_timestamp, instances=None, standard=True):
        candles = self._k.range_query_1(
            swap_timestamp,
            due_timestamp,
            KLINE_INTERVAL_1MIN,
            standard=standard
        )

        frag_candles = []
        instance = None
        for candle in candles:
            if len(frag_candles) == 0:
                frag_candles.append(candle)
                continue
            if frag_candles[0]["timestamp"] == candle["timestamp"]:
                frag_candles.append(candle)
                continue

            frag_candles = []
            instance = self.__compare_candles_with_instances(frag_candles, instances)
            if instance:
                return instance
        return instance

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
            self["param"].save(self["id"])
            self["indices"].save(self["id"])

        else:
            raise RuntimeError("I think can not insert in this place. ")

    # 判断是否触发，将结果返回，并将触发的instance信息合并到当前的对象上。
    def back_test_waiting(self, timestamp: int) -> dict:
        pass

    def back_test_opening(self, timestamp: int) -> dict:
        pass

    def back_test_liquidating(self, timestamp: int) -> dict:
        pass
