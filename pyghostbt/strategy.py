from typing import List
from typing import Tuple
from jsonschema import validate

from pyanalysis.mysql import Conn
from pyanalysis.moment import moment
from pyghostbt.tool.runtime import Runtime
from pyghostbt.tool.asset import Asset
from pyghostbt.tool.indices import Indices
from pyghostbt.tool.param import Param
from pyghostbt.tool.order import CommonOrder
from pyghostbt.tool.order import FutureOrder
from pyghostbt.util import get_contract_type
from pyghostbt.util import real_number
from pyghostbt.const import *
from pyghostbt.validate import INSTANCE_VALIDATE

strategy_input = {
    "type": "object",
    "required": ["strategy"],
    "properties": {
        "strategy": {
            "type": "string"
        },
        "id": {
            "type": "integer",
        },
    }
}


class Strategy(Runtime):
    def __init__(self, kw):
        super().__init__(kw)
        validate(instance=kw, schema=strategy_input)
        # 初始化各个组件

        self["asset"] = Asset(
            trade_type=self.get("trade_type"),
            symbol=self.get("symbol"),
            exchange=self.get("exchange"),
            db_name=self.get("db_name_asset") or self.get("db_name"),
            mode=self.get("mode"),
            settle_mode=self.get("settle_mode") or SETTLE_MODE_BASIS,
            backtest_id=self.get("backtest_id"),
        )

        self["indices"] = Indices(
            self.get("indices") or {},
            mode=self.get("mode"),
            trade_type=self.get("trade_type"),
            db_name=self.get("db_name"),
        )
        self["param"] = Param(
            self["param"],
            db_name=self.get("db_name_param") or self.get("db_name"),
            mode=self.get("mode"),
            trade_type=self.get("trade_type"),
        )

        instance_id = kw.get("id")
        if instance_id is not None:
            conn = Conn(self["db_name"])
            instance = conn.query_one(
                "SELECT * FROM {trade_type}_instance_{mode} WHERE id = ?".format(
                    trade_type=self["trade_type"],
                    mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY,
                ),
                (instance_id,),
            )

            self["strategy"] = instance["strategy"]
            self["interval"] = instance["interval"]
            self["unit_amount"] = instance["unit_amount"]
            self["param"] = self["param"].load(instance_id)
            self["indices"] = self["indices"].load(instance_id)

            if self["trade_type"] == TRADE_TYPE_FUTURE:
                self["lever"] = instance["lever"]
                self["status"] = instance["status"]

    @staticmethod
    def check_instance(instance):
        validate(instance=instance, schema=INSTANCE_VALIDATE)

    # 获取instance 风险等级。 timestamp要设置为interval的起始时间。
    def _get_risk_level(self, timestamp: int, instance_id: int) -> int:
        conn = Conn(self["db_name"])
        table_name = "{trade_type}_instance_{mode}".format(
            trade_type=self["trade_type"],
            mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY,
        )

        # m = moment.get(timestamp).to(self.get("timezone") or "Asia/Shanghai").floor("day")
        query_sql = """
        SELECT id FROM {} WHERE symbol = ? AND exchange = ? AND strategy = ? 
        AND (status IN (?, ?, ?) OR ( status = ? AND liquidate_finish_timestamp > ? )) ORDER BY open_start_timestamp, id
        """
        params = (
            self["symbol"], self["exchange"], self["strategy"],
            INSTANCE_STATUS_OPENING, INSTANCE_STATUS_LIQUIDATING, INSTANCE_STATUS_ERROR,
            INSTANCE_STATUS_FINISHED, timestamp,
        )

        if self["mode"] == MODE_BACKTEST:
            query_sql = """
            SELECT id FROM {} WHERE backtest_id = ? AND symbol = ? AND exchange = ?
             AND strategy = ? AND open_start_timestamp < ? AND (liquidate_finish_timestamp > ? OR status in (?,?)) 
             ORDER BY open_start_timestamp, id
            """
            params = (
                self["backtest_id"],
                self["symbol"],
                self["exchange"],
                self["strategy"],
                timestamp,
                timestamp,
                INSTANCE_STATUS_OPENING,
                INSTANCE_STATUS_LIQUIDATING,
            )
        instances = conn.query(
            query_sql.format(table_name),
            params,
        )

        # instance_ids = [i["id"] for i in instances]
        # risk_level = len(instance_ids)
        # if instance_id in instance_ids:
        #     risk_level = instance_ids.index(instance_id)
        return len(instances)

    def _get_waiting_instance_id(self) -> int:
        query_sql = """
        SELECT id FROM {trade_type}_instance_strategy WHERE symbol = ? AND exchange = ? AND strategy = ?
        AND status = ? AND wait_start_timestamp = ? ORDER BY id DESC LIMIT 1
        """
        params = (
            self["symbol"], self["exchange"], self["strategy"],
            INSTANCE_STATUS_WAITING, 0,
        )

        if self["trade_type"] == TRADE_TYPE_FUTURE:
            query_sql = """
            SELECT id FROM {trade_type}_instance_strategy WHERE symbol = ? AND exchange = ? 
            AND contract_type = ? AND strategy = ? AND status = ? AND wait_start_timestamp = ? ORDER BY id DESC LIMIT 1
            """
            params = (
                self["symbol"], self["exchange"], self["contract_type"],
                self["strategy"], INSTANCE_STATUS_WAITING, 0,
            )

        conn = Conn(self["db_name"])
        one = conn.query_one(
            query_sql.format(trade_type=self["trade_type"]),
            params,
        )
        return one["id"] if one else 0

    def _is_opened(self, wait_start_timestamp: int) -> bool:
        conn = Conn(self["db_name"])
        if self["trade_type"] == TRADE_TYPE_FUTURE:
            opened = conn.query(
                "SELECT id FROM future_instance_{mode} WHERE symbol = ? AND exchange = ? AND contract_type = ?"
                " AND strategy = ? AND wait_start_timestamp = ? AND status > ?".format(
                    mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY,
                ),
                (
                    self["symbol"], self["exchange"], self["contract_type"], self["strategy"],
                    wait_start_timestamp, INSTANCE_STATUS_WAITING,
                ),
            )
            return len(opened) > 0

        opened = conn.query(
            "SELECT id FROM {trade_type}_instance_{mode} WHERE symbol = ? AND exchange = ? AND strategy = ? "
            "AND wait_start_timestamp = ? AND status > ?".format(
                trade_type=self["trade_type"],
                mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY,
            ),
            (
                self["symbol"], self["exchange"], self["strategy"],
                wait_start_timestamp, INSTANCE_STATUS_WAITING,
            ),
        )
        return len(opened) > 0

    def get_waiting(self, timestamp) -> (List[dict], str):
        self.__setitem__("id", self._get_waiting_instance_id())
        return [], ""

    def get_opening(self, timestamp: int) -> list:
        if self["mode"] not in (MODE_BACKTEST, MODE_STRATEGY):
            self["mode"] = MODE_STRATEGY

        if self["mode"] == MODE_STRATEGY:
            self.load_from_db(self["id"])
        return []

    def get_liquidating(self, timestamp: int) -> list:
        if self["mode"] not in (MODE_BACKTEST, MODE_STRATEGY):
            self["mode"] = MODE_STRATEGY

        if self["mode"] == MODE_STRATEGY:
            self.load_from_db(self["id"])
        return []

    def get_instances(self, timestamp):
        if self["status"] == INSTANCE_STATUS_WAITING:
            waits, _ = self.get_waiting(timestamp)
            return waits
        elif self["status"] == INSTANCE_STATUS_OPENING:
            return self.get_opening(timestamp)
        elif self["status"] == INSTANCE_STATUS_LIQUIDATING:
            return self.get_liquidating(timestamp)
        else:
            raise RuntimeError("Can not recognise the instance status")

    # 根据 instance参数更新当前的对象的属性。
    def load_from_memory(self, instance):
        if self["id"] != instance["id"]:
            raise RuntimeError("the ")

        self["status"] = instance["status"]
        self["unit_amount"] = instance.get("unit_amount") or 1

        self["asset_total"] = instance["asset_total"]
        self["asset_freeze"] = instance["asset_freeze"]

        self["param_position"] = instance["param_position"]
        self["param_max_abs_loss_ratio"] = instance["param_max_abs_loss_ratio"]

        self["wait_start_timestamp"] = instance["wait_start_timestamp"]
        self["wait_start_datetime"] = instance["wait_start_datetime"]
        self["wait_finish_timestamp"] = instance["wait_finish_timestamp"]
        self["wait_finish_datetime"] = instance["wait_finish_datetime"]

        self["open_times"] = instance["open_times"]
        self["open_start_timestamp"] = instance["open_start_timestamp"]
        self["open_start_datetime"] = instance["open_start_datetime"]
        self["open_finish_timestamp"] = instance["open_finish_timestamp"]
        self["open_finish_datetime"] = instance["open_finish_datetime"]
        self["open_expired_timestamp"] = instance["open_expired_timestamp"]
        self["open_expired_datetime"] = instance["open_expired_datetime"]

        self["liquidate_times"] = instance["liquidate_times"]
        self["liquidate_start_timestamp"] = instance["liquidate_start_timestamp"]
        self["liquidate_start_datetime"] = instance["liquidate_start_datetime"]
        self["liquidate_finish_timestamp"] = instance["liquidate_finish_timestamp"]
        self["liquidate_finish_datetime"] = instance["liquidate_finish_datetime"]

        self["order"] = instance["order"]
        self["param"] = Param(
            instance.get("param") or {},
            trade_type=self["trade_type"],
            db_name=self["db_name"],
            mode=self["mode"],
        )
        self["indices"] = Indices(
            instance.get("indices") or {},
            trade_type=self["trade_type"],
            db_name=self["db_name"],
            mode=self["mode"],
        )

    def load_from_db(self, instance_id):
        conn = Conn(self["db_name"])
        tmp_instance = conn.query_one(
            "SELECT * FROM {trade_type}_instance_{mode} WHERE id = ?".format(
                trade_type=self["trade_type"],
                mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY,
            ),
            (instance_id,),
        )

        if tmp_instance is None:
            raise RuntimeError("the instance is None. ")

        self["id"] = tmp_instance["id"]
        self["status"] = tmp_instance["status"]
        self["unit_amount"] = tmp_instance.get("unit_amount") or 1

        self["asset_total"] = tmp_instance["asset_total"]
        self["asset_freeze"] = tmp_instance["asset_freeze"]

        self["param_position"] = tmp_instance["param_position"]
        self["param_max_abs_loss_ratio"] = tmp_instance["param_max_abs_loss_ratio"]

        self["wait_start_timestamp"] = tmp_instance["wait_start_timestamp"]
        self["wait_start_datetime"] = tmp_instance["wait_start_datetime"]
        self["wait_finish_timestamp"] = tmp_instance["wait_finish_timestamp"]
        self["wait_finish_datetime"] = tmp_instance["wait_finish_datetime"]

        self["open_times"] = tmp_instance["open_times"]
        self["open_start_timestamp"] = tmp_instance["open_start_timestamp"]
        self["open_start_datetime"] = tmp_instance["open_start_datetime"]
        self["open_finish_timestamp"] = tmp_instance["open_finish_timestamp"]
        self["open_finish_datetime"] = tmp_instance["open_finish_datetime"]
        self["open_expired_timestamp"] = tmp_instance["open_expired_timestamp"]
        self["open_expired_datetime"] = tmp_instance["open_expired_datetime"]

        self["liquidate_times"] = tmp_instance["liquidate_times"]
        self["liquidate_start_timestamp"] = tmp_instance["liquidate_start_timestamp"]
        self["liquidate_start_datetime"] = tmp_instance["liquidate_start_datetime"]
        self["liquidate_finish_timestamp"] = tmp_instance["liquidate_finish_timestamp"]
        self["liquidate_finish_datetime"] = tmp_instance["liquidate_finish_datetime"]

        param = Param(
            {},
            trade_type=self["trade_type"],
            db_name=self["db_name"],
            mode=self["mode"],
        )
        param.load(instance_id)
        self["param"] = param

        indices = Indices(
            {},
            trade_type=self["trade_type"],
            db_name=self["db_name"],
            mode=self["mode"],
        )
        indices.load(instance_id)
        self["indices"] = indices

    def _get_orders(self) -> List:
        conn = Conn(self["db_name"])
        orders = conn.query(
            "SELECT * FROM {trade_type}_order_{mode} WHERE instance_id = ?"
            " ORDER BY sequence".format(
                trade_type=self["trade_type"],
                mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY,
            ),
            (self["id"])
        )
        return orders

    def _analysis_orders(self, due_ts: int) -> tuple:
        """
        :param
            due_ts: the due timestamp now.

        :return

            start_sequence: next sequence
            opening_avg_price: the opening avg price in instance.
            order price array: the orders price of instance.
            order amount array: the orders amount of instance.
            opening_amount map with due_ts: {due_ts: opening_amount}
            opening_quota map with due_ts: {due_ts: opening_quota}

        """

        orders = self._get_orders()
        if len(orders) == 0:
            return -1, 0, 0, [], [], {}, {}

        opened_times = 0
        opened_quota = 0
        start_sequence = orders[-1]["sequence"] + 1
        opened_prices = []
        opened_amounts = []

        # spot swap margin 交易没有due_timestamp的概念，故设置为0
        if due_ts is None:
            due_ts = 0
        opening_amounts, opening_quota = {due_ts: 0}, {due_ts: 0}

        for order in orders:
            if order.get("status") == ORDER_STATUS_FAIL:
                return -1, 0, 0, [], [], {}, {}
            if order.get("status") == ORDER_STATUS_UNFINISH:
                return -1, 0, 0, [], [], {}, {}

            order_due_ts = order.get("due_timestamp") or 0
            if order_due_ts not in opening_amounts:
                opening_amounts[order_due_ts] = 0
                opening_quota[order_due_ts] = 0

            if order["type"] in (ORDER_TYPE_OPEN_LONG, ORDER_TYPE_OPEN_SHORT):
                opening_amounts[order_due_ts] += order["deal_amount"]
                opening_quota[order_due_ts] += order["deal_amount"] * order["avg_price"]
                opened_quota += order["deal_amount"] * order["avg_price"]
                if order["place_type"] != ORDER_PLACE_TYPE_O_SWAP:
                    opened_prices.append(order["price"])
                    opened_amounts.append(order["amount"])
                    opened_times += 1
            elif order["type"] in (ORDER_TYPE_LIQUIDATE_LONG, ORDER_TYPE_LIQUIDATE_SHORT):
                opening_amounts[order_due_ts] -= order["deal_amount"]
                opened_quota -= order["deal_amount"] * order["avg_price"]
                if opening_amounts[order_due_ts] == 0:
                    opening_quota[order_due_ts] = 0
                else:
                    opening_quota[order_due_ts] -= order["deal_amount"] * order["avg_price"]
            else:
                raise RuntimeError("Not found the order type")

        opening_amount = sum([opening_amounts[ts] for ts in opening_amounts])
        opening_avg_price = 0
        if opening_amount > 0:
            opening_avg_price = opened_quota / opening_amount
        return start_sequence, opened_times, opening_avg_price, opened_prices, opened_amounts, opening_amounts, opening_quota

    def _settle_pnl(self, settle_mode=SETTLE_MODE_BASIS) -> Tuple[bool, float]:
        orders = self._get_orders()
        settle_pnl, total_fee = 0.0, 0.0
        open_amount, liquidate_amount = 0, 0
        unit_amount: float = self.get("unit_amount") or 1.0
        contract_kv = {}

        for order in orders:
            if order["status"] == ORDER_STATUS_FAIL:
                return False, 0.0
            due_timestamp: int = order.get("due_timestamp") or 0  # the spot or swap or margin have no due_timestamp
            avg_price = real_number(order["avg_price"])
            total_fee += order["fee"]
            if due_timestamp not in contract_kv:
                contract_kv[due_timestamp] = {
                    "open_amount": 0,
                    "open_quota": 0,

                    "liquidate_amount": 0,
                    "liquidate_quota": 0,
                }

            if order["type"] == ORDER_TYPE_OPEN_LONG:
                open_amount += order["deal_amount"]
                contract = contract_kv[due_timestamp]
                contract["open_amount"] += order["deal_amount"]
                if unit_amount > 1.0 or unit_amount < 1.0:
                    contract["open_quota"] -= order["deal_amount"] * avg_price * unit_amount
                else:
                    contract["open_quota"] -= real_number(order["deal_amount"]) * avg_price
            elif order["type"] == ORDER_TYPE_OPEN_SHORT:
                open_amount += order["deal_amount"]
                contract = contract_kv[due_timestamp]
                contract["open_amount"] += order["deal_amount"]
                if unit_amount > 1.0 or unit_amount < 1.0:
                    contract["open_quota"] += order["deal_amount"] * avg_price * unit_amount
                else:
                    contract["open_quota"] += real_number(order["deal_amount"]) * avg_price
            elif order["type"] == ORDER_TYPE_LIQUIDATE_LONG:
                liquidate_amount += order["deal_amount"]
                contract = contract_kv[due_timestamp]
                contract["liquidate_amount"] += order["deal_amount"]
                if unit_amount > 1.0 or unit_amount < 1.0:
                    contract["liquidate_quota"] += order["deal_amount"] * avg_price * unit_amount
                else:
                    contract["liquidate_quota"] += real_number(order["deal_amount"]) * avg_price
            elif order["type"] == ORDER_TYPE_LIQUIDATE_SHORT:
                liquidate_amount += order["deal_amount"]
                contract = contract_kv[due_timestamp]
                contract["liquidate_amount"] += order["deal_amount"]
                if unit_amount > 1.0 or unit_amount < 1.0:
                    contract["liquidate_quota"] -= order["deal_amount"] * avg_price * unit_amount
                else:
                    contract["liquidate_quota"] -= real_number(order["deal_amount"]) * avg_price
            else:
                raise RuntimeError("the order type is not right. ")

        if open_amount != liquidate_amount:
            return False, 0.0

        # 计算各个contract的盈利损失情况。
        for d in contract_kv:
            contract = contract_kv[d]
            if contract["open_amount"] != contract["liquidate_amount"]:
                return False, 0.0

            contract_settle_pnl = contract["liquidate_quota"] + contract["open_quota"]
            if settle_mode == SETTLE_MODE_BASIS:
                # 除以open_price
                contract_settle_pnl /= abs(contract["open_quota"] / contract["open_amount"] / unit_amount)
                # 除以liquidate_price
                contract_settle_pnl /= abs(contract["liquidate_quota"] / contract["liquidate_amount"] / unit_amount)
            settle_pnl += contract_settle_pnl
        return True, settle_pnl + total_fee

    def _cp_instance_and_gen_order(
            self,
            sequence: int,  # 所属顺序
            timestamp: int,  # 策略产生的时间戳
            due_timestamp: int,  # 对用contract的到期时间
            price: int,  # 标准化价格
            amount: int,  # 开仓/平仓数量
            order_type: int,  # 交易类型
            place_type: str,  # 下单手法
    ):

        instance = self.copy()
        param: Param = Param(
            self["param"].copy(),
            trade_type=self["trade_type"],
            db_name=self["db_name"],
            mode=self["mode"],
        )
        indices: Indices = Indices(
            self["indices"].copy(),
            trade_type=self["trade_type"],
            db_name=self["db_name"],
            mode=self["mode"],
        )
        instance["param"] = param
        instance["indices"] = indices

        if self["trade_type"] == TRADE_TYPE_FUTURE:
            due_datetime = moment.get(due_timestamp).to(
                self["timezone"] or "Asia/Shanghai",
            ).format("YYYY-MM-DD HH:mm:ss")
            instance["order"] = FutureOrder(
                {
                    "place_type": place_type,
                    "type": order_type,
                    "symbol": self["symbol"],
                    "exchange": self["exchange"],
                    "contract_type": get_contract_type(timestamp, due_timestamp),
                    "instance_id": self["id"],
                    "sequence": sequence,
                    "price": int(price),
                    "amount": int(amount),
                    "lever": self["lever"],
                    "due_timestamp": due_timestamp,
                    "due_datetime": due_datetime,
                    "unit_amount": self["unit_amount"],
                },
                trade_type=self["trade_type"],
                db_name=self["db_name"],
                mode=self["mode"],
                settle_mode=self["settle_mode"]
            )
            return instance

        instance["order"] = CommonOrder(
            {
                "place_type": place_type,
                "type": order_type,
                "symbol": self["symbol"],
                "exchange": self["exchange"],
                "instance_id": self["id"],
                "sequence": sequence,
                "price": int(price),
                "amount": int(amount),
                "lever": self["lever"],
                "unit_amount": self.get("unit_amount") or 1,
            },
            trade_type=self["trade_type"],
            db_name=self["db_name"],
            mode=self["mode"],
            settle_mode=self["settle_mode"]
        )
        return instance

    def _get_previous_instances(self, start_timestamp=0, finish_timestamp=0):
        if start_timestamp == 0:
            raise RuntimeError("start_timestamp must bigger than 0. ")

        if finish_timestamp == 0:
            finish_timestamp = moment.now().millisecond_timestamp

        conn = Conn(self["db_name"])
        table_name = "{trade_type}_instance_{mode}".format(
            trade_type=self["trade_type"],
            mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY,
        )

        if self["trade_type"] == TRADE_TYPE_FUTURE:
            query_sql = """
            SELECT * FROM {} WHERE symbol = ? AND exchange = ? AND contract_type = ? AND strategy = ?
             AND wait_start_timestamp >= ? AND wait_start_timestamp < ? AND status != ? ORDER BY wait_start_timestamp
            """.format(table_name)
            query_param = (
                self["symbol"], self["exchange"], self["contract_type"], self["strategy"],
                start_timestamp, finish_timestamp, INSTANCE_STATUS_WAITING,
            )

            if self["mode"] == MODE_BACKTEST:
                query_sql = """
                        SELECT * FROM {} WHERE symbol = ? AND exchange = ? AND contract_type = ?
                        AND strategy = ? AND wait_start_timestamp >= ? AND wait_start_timestamp < ?
                        AND backtest_id = ? AND status != ? ORDER BY wait_start_timestamp
                """.format(table_name)

                query_param = (
                    self["symbol"], self["exchange"], self["contract_type"], self["strategy"],
                    start_timestamp, finish_timestamp, self["backtest_id"], INSTANCE_STATUS_WAITING,
                )
        else:
            query_sql = """
            SELECT * FROM {} WHERE symbol = ? AND exchange = ? AND strategy = ?
            AND wait_start_timestamp >= ? AND wait_start_timestamp < ? AND status != ?
            ORDER BY wait_start_timestamp 
            """.format(table_name)
            query_param = (
                self["symbol"], self["exchange"], self["strategy"],
                start_timestamp, finish_timestamp, INSTANCE_STATUS_WAITING,
            )

            if self["mode"] == MODE_BACKTEST:
                query_sql = """
                SELECT * FROM {} WHERE symbol = ? AND exchange = ? AND strategy = ?
                AND wait_start_timestamp >= ? AND wait_start_timestamp < ?
                AND backtest_id = ? AND status != ? ORDER BY wait_start_timestamp 
                """.format(table_name)
                query_param = (
                    self["symbol"], self["exchange"], self["strategy"],
                    start_timestamp, finish_timestamp, self["backtest_id"], INSTANCE_STATUS_WAITING,
                )
        return conn.query(query_sql, query_param)
