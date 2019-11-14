from jsonschema import validate
from pyghostbt.strategy import Strategy
from pyghostbt.const import *
from pyanalysis.mysql import Conn

instance_param = {
    "type": "object",
    "required": [
        "id", "symbol", "exchange", "strategy", "status", "interval", "wait_start_timestamp", "wait_start_datetime",
        "wait_finish_timestamp", "wait_finish_datetime", "total_asset", "sub_freeze_asset", "param_position",
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
        "wait_start_timestamp": {
            "type": "integer",
            "minimum": 1000000000000,
            "maximum": 3000000000000,
        },
        "wait_start_datetime": {
            "type": "string"
        },
        "wait_finish_timestamp": {
            "type": "integer",
            "minimum": 1000000000000,
            "maximum": 3000000000000,
        },
        "wait_finish_datetime": {
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
    def __init__(self, kw: dict):
        super().__init__(kw)

        # self._slippage = 0.01  # 滑点百分比
        # self._fee = -0.0005  # 手续费比例

    """
    单个蜡烛和交易逻辑比较
    """

    @staticmethod
    def __compare_candle_with_instance(candle: dict, instance: dict) -> dict:
        order = instance["order"]
        if order["place_type"] == ORDER_PLACE_TYPE_T_TAKER:
            if candle["high"] > order["price"]:
                order["place_timestamp"] = candle["timestamp"]
                order["place_datetime"] = candle["date"]
                order["deal_timestamp"] = candle["timestamp"]
                order["deal_datetime"] = candle["date"]
                order["due_timestamp"] = candle["due_timestamp"]
                order["due_datetime"] = candle["due_date"]
                return instance
        elif order["place_type"] == ORDER_PLACE_TYPE_B_TAKER:
            if candle["low"] < order["price"]:
                order["place_timestamp"] = candle["timestamp"]
                order["place_datetime"] = candle["date"]
                order["deal_timestamp"] = candle["timestamp"]
                order["deal_datetime"] = candle["date"]
                order["due_timestamp"] = candle["due_timestamp"]
                order["due_datetime"] = candle["due_date"]
                return instance
        else:
            raise RuntimeError("do not support the other place_type")
        return {}

    # TODO 同一个timestamp中不同的due_timestamp kline
    @staticmethod
    def __compare_candles_with_instances(candles: list, instances: list) -> list:
        candles_kv = {}
        for candle in candles:
            candles_kv[candle["due_timestamp"]] = candle
        l_price, o_price = None, None
        l_swap_instance, o_swap_instance = None, None
        for instance in instances:
            the_candle = candles_kv.get(instance["order"]["due_timestamp"])
            if instance["order"]["place_type"] == ORDER_PLACE_TYPE_L_SWAP:
                if the_candle:
                    l_price = the_candle["close"]
                    l_swap_instance = instance
            elif instance["order"]["place_type"] == ORDER_PLACE_TYPE_O_SWAP:
                if the_candle:
                    o_price = the_candle["close"]
                    o_swap_instance = instance
            else:
                if the_candle and Backtest.__compare_candle_with_instance(the_candle, instance):
                    return [instance]
        if l_price and o_price:
            if -0.03 < o_price / l_price - 1 < 0.03:
                return [l_swap_instance, o_swap_instance]
        return []

    def _back_test_by_min_kline(
            self,
            start_timestamp: int,
            finish_timestamp: int,
            instances=None,
            standard=True,
    ) -> dict:
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
        return {}

    def _back_test_swap_by_min_kline(
            self,
            swap_timestamp: int,
            due_timestamp: int,
            instances=None,
            standard=True,
    ) -> list:
        candles = self._k.range_query_all_contract(
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

    def _back_test_by_day_kline(
            self,
            start_timestamp: int,
            finish_timestamp: int,
            instances=None,
            standard=True,
    ) -> dict:
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
        return {}

    def save(self) -> None:
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
                "wait_start_timestamp = ?, wait_start_datetime = ?, "
                "wait_finish_timestamp = ?, wait_finish_datetime = ?, "
                "open_start_timestamp = ?, open_start_datetime = ?, "
                "open_finish_timestamp = ?, open_finish_datetime = ?, "
                "liquidate_start_timestamp = ?, liquidate_start_datetime = ?, "
                "liquidate_finish_timestamp = ?, liquidate_finish_datetime = ?, "
                "total_asset = ?, sub_freeze_asset = ?, param_position = ?, param_max_abs_loss = ? "
                "WHERE id = ?".format(trade_type=self["trade_type"], mode=self["mode"]),
                (
                    self["symbol"], self["exchange"], self["contract_type"], self["strategy"],
                    self["unit_amount"], self["lever"], self["status"], self["interval"],
                    self["wait_start_timestamp"], self["wait_start_datetime"],
                    self["wait_finish_timestamp"], self["wait_finish_datetime"],
                    self["open_start_timestamp"], self["open_start_datetime"],
                    self["open_finish_timestamp"], self["open_finish_datetime"],
                    self["liquidate_start_timestamp"], self["liquidate_start_datetime"],
                    self["liquidate_finish_timestamp"], self["liquidate_finish_datetime"],
                    self["total_asset"], self["sub_freeze_asset"], self["param_position"], self["param_max_abs_loss"],
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
