from typing import List
from jsonschema import validate

from pyanalysis.mysql import Conn
from pyanalysis.moment import moment
from pyghostbt.tool.runtime import Runtime
from pyghostbt.tool.asset import Asset
from pyghostbt.tool.indices import Indices
from pyghostbt.tool.param import Param
from pyghostbt.tool.order import FutureOrder
from pyghostbt.util import get_contract_type
from pyghostbt.const import *

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

instance_param = {
    "type": "object",
    "required": [
        "id", "symbol", "exchange", "strategy", "status", "interval",
        "total_asset", "sub_freeze_asset", "param_position", "param_max_abs_loss_ratio",
        "wait_start_timestamp", "wait_start_datetime",
        "wait_finish_timestamp", "wait_finish_datetime",
        "open_start_timestamp", "open_start_datetime",
        "open_finish_timestamp", "open_finish_datetime",
        "open_expired_timestamp", "open_expired_datetime",
        "liquidate_start_timestamp", "liquidate_start_datetime",
        "liquidate_finish_timestamp", "liquidate_finish_datetime",
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
        "open_start_timestamp": {
            "type": "integer",
        },
        "open_start_datetime": {
            "type": ["string", "null"],
        },
        "open_finish_timestamp": {
            "type": "integer",
        },
        "open_finish_datetime": {
            "type": ["string", "null"],
        },
        "open_expired_timestamp": {
            "type": "integer",
        },
        "open_expired_datetime": {
            "type": ["string", "null"],
        },
        "liquidate_start_timestamp": {
            "type": "integer",
        },
        "liquidate_start_datetime": {
            "type": ["string", "null"],
        },
        "liquidate_finish_timestamp": {
            "type": "integer",
        },
        "liquidate_finish_datetime": {
            "type": ["string", "null"],
        }
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
            contract_type=self.get("contract_type"),
            db_name=self.get("db_name_asset") or self.get("db_name"),
            mode=self.get("mode"),
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
            self["param"] = self["param"].load(instance_id)
            self["indices"] = self["indices"].load(instance_id)

            if self["trade_type"] == TRADE_TYPE_FUTURE:
                self["unit_amount"] = instance["unit_amount"]
                self["lever"] = instance["lever"]
                self["status"] = instance["status"]

    @staticmethod
    def check_instance(instance):
        validate(instance=instance, schema=instance_param)

    # 获取instance 风险等级。
    def _get_risk_level(self, timestamp: int, instance_id: int) -> int:
        conn = Conn(self["db_name"])
        table_name = "{trade_type}_instance_{mode}".format(
            trade_type=self["trade_type"],
            mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY,
        )
        query_sql = """
        SELECT id FROM {} WHERE symbol = ? AND exchange = ? AND strategy = ? 
        AND status in (?, ?) ORDER BY open_start_timestamp, id
        """
        params = (
            self["symbol"], self["exchange"], self["strategy"], INSTANCE_STATUS_OPENING, INSTANCE_STATUS_LIQUIDATING,
        )

        if self["mode"] == MODE_BACKTEST:
            query_sql = """
            SELECT id FROM {} WHERE backtest_id = ? AND symbol = ? AND exchange = ?
             AND strategy = ? AND open_start_timestamp < ? AND liquidate_finish_timestamp > ? 
             ORDER BY open_start_timestamp, id
            """
            params = (self["backtest_id"], self["symbol"], self["exchange"], self["strategy"], timestamp, timestamp)
        instances = conn.query(
            query_sql.format(table_name),
            params,
        )

        instance_ids = [i["id"] for i in instances]
        risk_level = len(instance_ids)
        if instance_id in instance_ids:
            risk_level = instance_ids.index(instance_id)
        return risk_level

    def _get_waiting_instance_id(self) -> int:
        conn = Conn(self["db_name"])
        query_sql = """
        SELECT id FROM {trade_type}_instance_{mode} WHERE symbol = ? AND exchange = ? AND strategy = ?
        AND status = ? AND wait_start_timestamp = ? ORDER BY id DESC LIMIT 1
        """
        params = (
            self["symbol"], self["exchange"], self["strategy"],
            INSTANCE_STATUS_WAITING, 0,
        )

        if self["trade_type"] == TRADE_TYPE_FUTURE:
            query_sql = """
            SELECT id FROM {trade_type}_instance_{mode} WHERE symbol = ? AND exchange = ? AND contract_type = ? 
            AND strategy = ? AND status = ? AND wait_start_timestamp = ? ORDER BY id DESC LIMIT 1
            """
            params = (
                self["symbol"], self["exchange"], self["contract_type"],
                self["strategy"], INSTANCE_STATUS_WAITING, 0,
            )
        item = conn.query_one(
            query_sql.format(trade_type=self["trade_type"], mode=self["mode"]),
            params
        )
        return item["id"] if item else 0

    def get_waiting(self, timestamp):
        # 原则：数据库中instance表中永远有一条 状态为 waiting状态的订单
        conn = Conn(self["db_name"])
        query_sql = """
        SELECT id FROM {trade_type}_instance_{mode} WHERE symbol = ? AND exchange = ? AND strategy = ?
         AND status = ? AND wait_start_timestamp = ?
        """
        insert_sql = """
        INSERT INTO {trade_type}_instance_{mode} (symbol, exchange, strategy, status, wait_start_timestamp)
         VALUES (?, ?, ?, ?, ?) 
        """
        params = (
            self["symbol"], self["exchange"], self["strategy"],
            INSTANCE_STATUS_WAITING, 0
        )

        if self["trade_type"] == TRADE_TYPE_FUTURE and self["mode"] == MODE_BACKTEST:
            query_sql = """
            SELECT id FROM {trade_type}_instance_{mode} WHERE symbol = ? AND exchange = ? AND contract_type = ?
             AND strategy = ? AND status = ? AND wait_start_timestamp = ? AND backtest_id = ?
            """
            insert_sql = """
            INSERT INTO {trade_type}_instance_{mode} (symbol, exchange, contract_type, strategy, status,
             wait_start_timestamp, backtest_id)
             VALUES (?, ?, ?, ?, ?, ?, ?) 
            """
            params = (
                self["symbol"], self["exchange"], self["contract_type"],
                self["strategy"], INSTANCE_STATUS_WAITING, 0, self["backtest_id"],
            )
        elif self["trade_type"] == TRADE_TYPE_FUTURE and self["mode"] in (MODE_OFFLINE, MODE_ONLINE):
            query_sql = """
            SELECT id FROM {trade_type}_instance_{mode} WHERE symbol = ? AND exchange = ? AND contract_type = ?
             AND strategy = ? AND status = ? AND wait_start_timestamp = ?
            """
            insert_sql = """
            INSERT INTO {trade_type}_instance_{mode} (symbol, exchange, contract_type, strategy, status,
             wait_start_timestamp) VALUES (?, ?, ?, ?, ?, ?) 
            """
            params = (
                self["symbol"], self["exchange"], self["contract_type"],
                self["strategy"], INSTANCE_STATUS_WAITING, 0,
            )

        # 线上环境中应该查找对应的instance记录来确定最新的 id
        item = conn.query_one(
            query_sql.format(
                trade_type=self["trade_type"],
                mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY,
            ),
            params
        )
        if item:
            self.__setitem__("id", item["id"])
        # 回测时生成对应的 id
        if self["mode"] == MODE_BACKTEST and item is None:
            last_insert_id = conn.insert(insert_sql.format(**self), params)
            self.__setitem__("id", last_insert_id)

    def get_opening(self, timestamp: int) -> list:
        pass

    def get_liquidating(self, timestamp: int) -> list:
        pass

    def get_instances(self, timestamp):
        if self["status"] == INSTANCE_STATUS_WAITING:
            return self.get_waiting(timestamp)
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
        self["total_asset"] = instance["total_asset"]
        self["sub_freeze_asset"] = instance["sub_freeze_asset"]

        self["param_position"] = instance["param_position"]
        self["param_max_abs_loss_ratio"] = instance["param_max_abs_loss_ratio"]

        self["wait_start_timestamp"] = instance["wait_start_timestamp"]
        self["wait_start_datetime"] = instance["wait_start_datetime"]
        self["wait_finish_timestamp"] = instance["wait_finish_timestamp"]
        self["wait_finish_datetime"] = instance["wait_finish_datetime"]

        self["open_start_timestamp"] = instance["open_start_timestamp"]
        self["open_start_datetime"] = instance["open_start_datetime"]
        self["open_finish_timestamp"] = instance["open_finish_timestamp"]
        self["open_finish_datetime"] = instance["open_finish_datetime"]
        self["open_expired_timestamp"] = instance["open_expired_timestamp"]
        self["open_expired_datetime"] = instance["open_expired_datetime"]

        self["liquidate_start_timestamp"] = instance["liquidate_start_timestamp"]
        self["liquidate_start_datetime"] = instance["liquidate_start_datetime"]
        self["liquidate_finish_timestamp"] = instance["liquidate_finish_timestamp"]
        self["liquidate_finish_datetime"] = instance["liquidate_finish_datetime"]

        self["order"] = instance["order"]
        self["param"] = instance["param"]
        self["indices"] = instance["indices"]

    # TODO 从数据库中读取对应的信息。
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
        self["total_asset"] = tmp_instance["total_asset"]
        self["sub_freeze_asset"] = tmp_instance["sub_freeze_asset"]

        self["param_position"] = tmp_instance["param_position"]
        self["param_max_abs_loss_ratio"] = tmp_instance["param_max_abs_loss_ratio"]

        self["wait_start_timestamp"] = tmp_instance["wait_start_timestamp"]
        self["wait_start_datetime"] = tmp_instance["wait_start_datetime"]
        self["wait_finish_timestamp"] = tmp_instance["wait_finish_timestamp"]
        self["wait_finish_datetime"] = tmp_instance["wait_finish_datetime"]

        self["open_start_timestamp"] = tmp_instance["open_start_timestamp"]
        self["open_start_datetime"] = tmp_instance["open_start_datetime"]
        self["open_finish_timestamp"] = tmp_instance["open_finish_timestamp"]
        self["open_finish_datetime"] = tmp_instance["open_finish_datetime"]
        self["open_expired_timestamp"] = tmp_instance["open_expired_timestamp"]
        self["open_expired_datetime"] = tmp_instance["open_expired_datetime"]

        self["liquidate_start_timestamp"] = tmp_instance["liquidate_start_timestamp"]
        self["liquidate_start_datetime"] = tmp_instance["liquidate_start_datetime"]
        self["liquidate_finish_timestamp"] = tmp_instance["liquidate_finish_timestamp"]
        self["liquidate_finish_datetime"] = tmp_instance["liquidate_finish_datetime"]

        param = Param({}, trade_type=self["trade_type"], db_name=self["db_name"], mode=self["mode"])
        param.load(instance_id)
        self["param"] = param

        indices = Indices({}, trade_type=self["trade_type"], db_name=self["db_name"], mode=self["mode"])
        indices.load(instance_id)
        self["indices"] = indices

    def _analysis_orders(self, due_ts: int) -> tuple:
        conn = Conn(self["db_name"])
        orders = conn.query(
            "SELECT * FROM {trade_type}_order_{mode}"
            " WHERE instance_id = ? ORDER BY sequence".format(
                trade_type=self["trade_type"],
                mode=MODE_BACKTEST if self["mode"] == MODE_BACKTEST else MODE_STRATEGY
            ),
            (self["id"],),
        )

        if len(orders) == 0:
            return ()

        opened_times = 0
        start_sequence = orders[-1]["sequence"] + 1
        opening_amounts, opening_sums = {due_ts: 0}, {due_ts: 0}
        for order in orders:
            order_due_ts = order["due_timestamp"]
            if order_due_ts not in opening_amounts:
                opening_amounts[order_due_ts] = 0
                opening_sums[order_due_ts] = 0

            if order["type"] in (ORDER_TYPE_OPEN_LONG, ORDER_TYPE_OPEN_SHORT):
                opening_amounts[order_due_ts] += order["deal_amount"]
                opening_sums[order_due_ts] += order["deal_amount"] * order["avg_price"]
                if order["place_type"] != ORDER_PLACE_TYPE_O_SWAP:
                    opened_times += 1
            elif order["type"] in (ORDER_TYPE_LIQUIDATE_LONG, ORDER_TYPE_LIQUIDATE_SHORT):
                opening_amounts[order_due_ts] -= order["deal_amount"]
                if opening_amounts[order_due_ts] == 0:
                    opening_sums[order_due_ts] = 0
                else:
                    opening_sums[order_due_ts] -= order["deal_amount"] * order["avg_price"]
            else:
                raise RuntimeError("Not found the order type")

        return (
            start_sequence,
            opened_times,
            orders[0]["price"],
            orders[0]["amount"],
            opening_amounts,
            opening_sums,
        )

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
        due_datetime = moment.get(due_timestamp).to(
            self["timezone"] or "Asia/Shanghai",
        ).format("YYYY-MM-DD HH:mm:ss")

        instance = self.copy()
        instance["order"] = FutureOrder(
            {
                "place_type": place_type,
                "type": order_type,
                "symbol": self["symbol"],
                "exchange": self["exchange"],
                "contract_type": get_contract_type(timestamp, due_timestamp),
                "instance_id": self["id"],
                "sequence": sequence,
                "price": price,
                "amount": amount,
                "lever": self["lever"],
                "due_timestamp": due_timestamp,
                "due_datetime": due_datetime,
                "unit_amount": self["unit_amount"],
            },
            trade_type=self["trade_type"],
            db_name=self["db_name"],
            mode=self["mode"],
        )
        return instance
