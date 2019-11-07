from pyanalysis.mysql import Conn
from pyghostbt.tool.runtime import Runtime
from pyghostbt.tool.asset import Asset
from pyghostbt.tool.indices import Indices
from pyghostbt.tool.param import Param
from pyghostbt.const import *
from jsonschema import validate

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
        "start_timestamp", "start_datetime", "finish_timestamp", "finish_datetime",
        "total_asset", "sub_freeze_asset", "param_position", "param_max_abs_loss",
        "open_timestamp", "open_datetime", "liquidate_timestamp", "liquidate_datetime",
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
        "open_timestamp": {
            "type": "integer",
        },
        "open_datetime": {
            "type": ["string", "null"],
        },
        "liquidate_timestamp": {
            "type": "integer",
        },
        "liquidate_datetime": {
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
                "SELECT * FROM {trade_type}_instance_{mode} WHERE id = ?".format(**self),
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

    def get_wait_open(self, timestamp):
        # 原则：数据库中instance表中永远有一条 状态为 wait_open的订单
        conn = Conn(self["db_name"])
        query_sql = """
        SELECT id FROM {trade_type}_instance_{mode} WHERE symbol = ? AND exchange = ? AND strategy = ?
         AND status = ? AND start_timestamp = ?
        """
        insert_sql = """
        INSERT INTO {trade_type}_instance_{mode} (symbol, exchange, strategy, status, start_timestamp)
         VALUES (?, ?, ?, ?, ?) 
        """
        params = (
            self["symbol"], self["exchange"], self["strategy"],
            INSTANCE_STATUS_WAIT_OPEN, 0
        )

        if self["trade_type"] == TRADE_TYPE_FUTURE:
            query_sql = """
            SELECT id FROM {trade_type}_instance_{mode} WHERE symbol = ? AND exchange = ? AND contract_type = ?
             AND strategy = ? AND status = ? AND start_timestamp = ? AND backtest_id = ?
            """
            insert_sql = """
            INSERT INTO {trade_type}_instance_{mode} (symbol, exchange, contract_type, strategy, status,
             start_timestamp, backtest_id)
             VALUES (?, ?, ?, ?, ?, ?, ?) 
            """
            params = (
                self["symbol"], self["exchange"], self["contract_type"],
                self["strategy"], INSTANCE_STATUS_WAIT_OPEN, 0, self["backtest_id"],
            )
        # 线上环境中应该查找对应的instance记录来确定最新的 id
        item = conn.query_one(query_sql.format(**self), params)
        if item:
            self.__setitem__("id", item["id"])
        # 回测时生成对应的 id
        if self["mode"] == MODE_BACKTEST and item is None:
            last_insert_id = conn.insert(insert_sql.format(**self), params)
            self.__setitem__("id", last_insert_id)

    def get_opening(self, timestamp):
        pass

    def get_wait_liquidate(self, timestamp):
        pass

    def get_liquidating(self, timestamp):
        pass

    # 根据 instance参数更新当前的对象的属性。
    def load(self, instance):
        if self["id"] != instance["id"]:
            raise RuntimeError("the ")

        self["status"] = instance["status"]
        self["start_timestamp"] = instance["start_timestamp"]
        self["start_datetime"] = instance["start_datetime"]
        self["finish_timestamp"] = instance["finish_timestamp"]
        self["finish_datetime"] = instance["finish_datetime"]
        self["total_asset"] = instance["total_asset"]
        self["sub_freeze_asset"] = instance["sub_freeze_asset"]

        self["param_position"] = instance["param_position"]
        self["param_max_abs_loss"] = instance["param_max_abs_loss"]

        self["open_timestamp"] = instance["open_timestamp"]
        self["open_datetime"] = instance["open_datetime"]

        self["liquidate_timestamp"] = instance["liquidate_timestamp"]
        self["liquidate_datetime"] = instance["liquidate_datetime"]

        self["order"] = instance["order"]
