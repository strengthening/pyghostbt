import json

from typing import List
from typing import Dict
from pyghostbt.strategy import Strategy
from pyghostbt.tool.order import FutureOrder
from pyghostbt.tool.param import Param
from pyghostbt.tool.indices import Indices
from pyghostbt.tool.asset import Asset
from pyghostbt.const import *
from pyanalysis.mysql import Conn

instance_param = {
    "type": "object",
    "required": [
        "id", "symbol", "exchange", "strategy", "status", "interval",
        "wait_start_timestamp", "wait_start_datetime", "wait_finish_timestamp", "wait_finish_datetime",
        "total_asset", "sub_freeze_asset", "param_position", "param_max_abs_loss_ratio",
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
        "param_max_abs_loss_ratio": {
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

    @staticmethod
    def __compare_candle_with_instance(candle: dict, instance: dict) -> dict:
        """
        单个蜡烛和数据交易逻辑比较
        """
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
            raise RuntimeError("do not support the other place_type", order["place_type"])
        return {}

    @staticmethod
    def __compare_candles_with_instances(candles: list, instances: list) -> list:
        """
        同一个timestamp不同的contract的蜡烛数据和交易逻辑进行比较。
        """
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
                    l_swap_instance["order"]["price"] = l_price  # add the candle close price to order
                    l_swap_instance["order"]["place_timestamp"] = the_candle["timestamp"]
                    l_swap_instance["order"]["place_datetime"] = the_candle["date"]
                    l_swap_instance["order"]["deal_timestamp"] = the_candle["timestamp"]
                    l_swap_instance["order"]["deal_datetime"] = the_candle["date"]
            elif instance["order"]["place_type"] == ORDER_PLACE_TYPE_O_SWAP:
                if the_candle:
                    o_price = the_candle["close"]
                    o_swap_instance = instance
                    o_swap_instance["order"]["price"] = o_price  # add the candle close price to order
                    o_swap_instance["order"]["place_timestamp"] = the_candle["timestamp"]
                    o_swap_instance["order"]["place_datetime"] = the_candle["date"]
                    o_swap_instance["order"]["deal_timestamp"] = the_candle["timestamp"]
                    o_swap_instance["order"]["deal_datetime"] = the_candle["date"]
            else:
                if the_candle and Backtest.__compare_candle_with_instance(the_candle, instance):
                    return [instance]
        if l_price and o_price:
            if -0.03 < o_price / l_price - 1 < 0.03:
                return [l_swap_instance, o_swap_instance]
        return []

    # 多个timestamp的多个contract的蜡烛数据，跟instance比较。
    @staticmethod
    def __compare_candles_kv_with_instances(
            candles_kv: Dict[int, Dict[int, dict]],
            instances: List[dict],
    ) -> List[dict]:
        contracts_kv: Dict[int, List[dict]] = {}  # record due_timestamp with the candles
        flag = 0
        candle_timestamps = sorted(candles_kv.keys(), reverse=True)
        for timestamp in candle_timestamps:
            for instance in instances:
                # 说明instance中有些contract的candle数据没有，放弃此
                if instance["order"]["due_timestamp"] not in candles_kv[timestamp]:
                    break
            else:
                for due_timestamp in candles_kv[timestamp]:
                    if due_timestamp not in contracts_kv:
                        contracts_kv[due_timestamp] = []
                    contracts_kv[due_timestamp].append(candles_kv[timestamp][due_timestamp])
                flag += 1

        l_avg_price, o_avg_price = 0.0, 0.0
        l_price, o_price = 0.0, 0.0
        l_swap_instance, o_swap_instance = None, None
        for instance in instances:
            the_candles = contracts_kv.get(instance["order"]["due_timestamp"])
            if instance["order"]["place_type"] == ORDER_PLACE_TYPE_L_SWAP:
                if flag < 15:  # 说明有超过15个蜡烛数据
                    continue
                l_price = the_candles[0]["close"]
                l_avg_price = sum([candle["close"] for candle in the_candles[:15]]) / 15
                l_swap_instance = instance
                l_swap_instance["order"]["price"] = l_price  # add the candle close price to order
                l_swap_instance["order"]["place_timestamp"] = the_candles[0]["timestamp"]
                l_swap_instance["order"]["place_datetime"] = the_candles[0]["date"]
                l_swap_instance["order"]["deal_timestamp"] = the_candles[0]["timestamp"]
                l_swap_instance["order"]["deal_datetime"] = the_candles[0]["date"]
            elif instance["order"]["place_type"] == ORDER_PLACE_TYPE_O_SWAP:
                if flag < 15:  # 说明有超过15个蜡烛数据
                    continue
                o_price = the_candles[0]["close"]
                o_avg_price = sum([candle["close"] for candle in the_candles[:15]]) / 15
                o_swap_instance = instance
                o_swap_instance["order"]["price"] = o_price
                o_swap_instance["order"]["place_timestamp"] = the_candles[0]["timestamp"]
                o_swap_instance["order"]["place_datetime"] = the_candles[0]["date"]
                o_swap_instance["order"]["deal_timestamp"] = the_candles[0]["timestamp"]
                o_swap_instance["order"]["deal_datetime"] = the_candles[0]["date"]
            else:
                # 除了swap的订单进行匹配。
                the_candle = candles_kv[candle_timestamps[0]].get(instance["order"]["due_timestamp"])
                if the_candle and Backtest.__compare_candle_with_instance(
                        the_candle,
                        instance,
                ):
                    return [instance]
        if l_price and o_price and l_avg_price and o_avg_price:
            if (-0.03 < o_price / l_price - 1 < 0.03) and (-0.03 < o_avg_price / l_avg_price - 1 < 0.03):
                return [l_swap_instance, o_swap_instance]
        return []

    def _back_test_by_min_kline(
            self,
            start_timestamp: int,
            finish_timestamp: int,
            instances: List[Dict] = None,
            standard: bool = True,
    ) -> dict:
        candles = self._kline.query_range(
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
            start_timestamp: int,
            finish_timestamp: int,
            instances: list = None,
            standard: bool = True,
    ) -> List[dict]:
        candles = self._kline.query_range_contracts(
            start_timestamp,
            finish_timestamp,
            KLINE_INTERVAL_1MIN,
            standard=standard
        )

        frag_candles_kv: Dict[int, Dict[int, dict]] = {}  # the key is timestamp, due_timestamp, value is candle
        tmp_instances: List[dict] = []  # 触发后的instances
        last_timestamp = 0

        for candle in candles:
            if len(frag_candles_kv) >= 15 and candle["timestamp"] != last_timestamp:
                tmp_instances = self.__compare_candles_kv_with_instances(frag_candles_kv, instances)
                if tmp_instances:
                    break

            if candle["timestamp"] != last_timestamp:
                frag_candles_kv[candle["timestamp"]] = {}

            last_timestamp = candle["timestamp"]
            frag_candles_kv[candle["timestamp"]][candle["due_timestamp"]] = candle
        else:
            if len(frag_candles_kv) >= 15:
                tmp_instances = self.__compare_candles_kv_with_instances(frag_candles_kv, instances)
        return tmp_instances

    def _back_test_by_day_kline(
            self,
            start_timestamp: int,
            finish_timestamp: int,
            instances=None,
            standard=True,
    ) -> dict:
        candles = self._kline.query(
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
                "open_expired_timestamp = ?, open_expired_datetime = ?, "
                "liquidate_start_timestamp = ?, liquidate_start_datetime = ?, "
                "liquidate_finish_timestamp = ?, liquidate_finish_datetime = ?, "
                "total_asset = ?, sub_freeze_asset = ?, param_position = ?, param_max_abs_loss_ratio = ? "
                "WHERE id = ?".format(trade_type=self["trade_type"], mode=self["mode"]),
                (
                    self["symbol"], self["exchange"], self["contract_type"], self["strategy"],
                    self["unit_amount"], self["lever"], self["status"], self["interval"],
                    self["wait_start_timestamp"], self["wait_start_datetime"],
                    self["wait_finish_timestamp"], self["wait_finish_datetime"],
                    self["open_start_timestamp"], self["open_start_datetime"],
                    self["open_finish_timestamp"], self["open_finish_datetime"],
                    self["open_expired_timestamp"], self["open_expired_datetime"],
                    self["liquidate_start_timestamp"], self["liquidate_start_datetime"],
                    self["liquidate_finish_timestamp"], self["liquidate_finish_datetime"],
                    self["total_asset"], self["sub_freeze_asset"], self["param_position"],
                    self["param_max_abs_loss_ratio"],
                    self["id"],
                ),
            )

            order: FutureOrder = self["order"]
            order.deal()
            order.save(
                check=True,
                raw_order_data=json.dumps(self),
            )

            param: Param = self["param"]
            param.save(self["id"])

            indices: Indices = self["indices"]
            indices.save(self["id"])
        else:
            raise RuntimeError("I think can not insert in this place. ")

    def _opening_expired(self, due_ts: int) -> int:
        """opening阶段超时过后，转到liquidating 或者finished阶段。
        Args:
            due_ts: The current contract due timestamp.

        Returns:
            The next stage starting timestamp.
        """
        (_, _, _, _, opening_amounts, _) = self._analysis_orders(due_ts)
        instance_status = INSTANCE_STATUS_LIQUIDATING
        for ts in opening_amounts:
            if opening_amounts[ts] > 0:
                break
        else:
            # 如果没有一个contract中有持仓，则认为交易结束。
            instance_status = INSTANCE_STATUS_FINISHED

        conn = Conn(self["db_name"])
        conn.execute(
            "UPDATE {trade_type}_instance_backtest SET wait_finish_timestamp = ?, wait_finish_datetime = ?,"
            " status = ? WHERE id = ?".format(trade_type=self["trade_type"]),
            (
                self["open_expired_timestamp"],
                self["open_expired_datetime"],
                instance_status,
                self["id"],
            ),
        )
        self["status"] = instance_status
        # 还有未平的仓位时
        if instance_status == INSTANCE_STATUS_LIQUIDATING:
            return self["open_expired_timestamp"]

        # 已经完成平仓时，这时属于finish阶段
        # 步骤一： 解冻对应的资产。
        asset: Asset = self["asset"]
        place_timestamp = self["open_expired_timestamp"]
        asset.unfreeze(self["sub_freeze_asset"], -self["param"]["position"], place_timestamp)
        # 步骤二： 记录对应损益。
        income_amount = asset.calculate_income(self["id"], self["unit_amount"], standard=True)
        asset.income(income_amount, place_timestamp)

        conn = Conn(self["db_name"])
        conn.execute(
            "UPDATE {}_instance_backtest SET total_pnl_asset = ? WHERE id = ?".format(self["trade_type"]),
            (
                income_amount,
                self["id"],
            )
        )
        return 0

    # 返回结果为该阶段结束时间，如果返回0表示该阶段没有触发
    def back_test_waiting(self, bt_wait_start_timestamp: int) -> int:
        pass

    def back_test_opening(self, bt_open_start_timestamp: int) -> int:
        pass

    def back_test_liquidating(self, bt_liquidate_start_timestamp: int) -> int:
        pass
