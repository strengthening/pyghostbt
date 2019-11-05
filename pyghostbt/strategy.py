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
                (instance_id, ),
            )

            self["strategy"] = instance["strategy"]
            self["interval"] = instance["interval"]
            self["param"] = self["param"].load(instance_id)
            self["indices"] = self["indices"].load(instance_id)

            if self["trade_type"] == TRADE_TYPE_FUTURE:
                self["unit_amount"] = instance["unit_amount"]
                self["lever"] = instance["lever"]
                self["status"] = instance["status"]

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
