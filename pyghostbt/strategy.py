from pyanalysis.mysql import Conn
from pyghostbt.tool.runtime import Runtime
from pyghostbt.const import *
from jsonschema import validate

strategy_input = {
    "type": "object",
    "required": ["strategy"],
    "properties": {
        "strategy": {
            "type": "string"
        },
    }
}


class Strategy(Runtime):
    def __init__(self, kw):
        super().__init__(kw)
        validate(instance=kw, schema=strategy_input)
        self._o = None

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
