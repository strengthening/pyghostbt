from jsonschema import validate
from pyanalysis.mysql import Conn
from pyghostbt.const import *

kline_input = {
    "type": "object",
    "required": ["trade_type", "symbol", "exchange", "db_name"],
    "properties": {
        "trade_type": {
            "type": "string",
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT],
        },
        "symbol": {
            "type": "string",
            "minLength": 1,
        },
        "exchange": {
            "type": "string",
            "enum": [EXCHANGE_OKEX, EXCHANGE_HUOBI, EXCHANGE_BINANCE],
        },
        "contract_type": {
            "type": "string",
            "enum": [CONTRACT_TYPE_THIS_WEEK, CONTRACT_TYPE_NEXT_WEEK, CONTRACT_TYPE_QUARTER],
        },
        "db_name": {
            "type": "string",
            "minLength": 1,
        }
    }
}


class Kline(object):
    __TABLE_NAME_FORMAT__ = "{trade_type}_kline_{symbol}"

    def __init__(self, **kwargs):
        super().__init__()

        validate(instance=kwargs, schema=kline_input)

        self.symbol = kwargs.get("symbol")
        self.exchange = kwargs.get("exchange")
        self.trade_type = kwargs.get("trade_type")
        self.contract_type = kwargs.get("contract_type")

        self.db_name = kwargs.get("db_name", "default")
        self.table_name = self.__TABLE_NAME_FORMAT__.format(
            trade_type=self.trade_type,
            symbol=self.symbol,
        )

        self.sql = """SELECT * FROM {} WHERE symbol = ? AND exchange = ?{}
         AND `interval` = ? AND timestamp >= ? AND timestamp < ? 
         ORDER BY timestamp LIMIT 100
        """.format(
            self.table_name,
            "" if self.trade_type != TRADE_TYPE_FUTURE else " AND contract_type = ? ",
        )

    @staticmethod
    def __standard_number(the_number):
        """将行情数据放大100000000倍，并四舍五入转化成int"""
        return int(the_number * 100000000 + 0.5)

    def __standard_candle(self, candle):
        candle["open"] = self.__standard_number(candle["open"])
        candle["high"] = self.__standard_number(candle["high"])
        candle["low"] = self.__standard_number(candle["low"])
        candle["close"] = self.__standard_number(candle["close"])
        return candle

    def raw_query(self, start_timestamp, finish_timestamp, interval, standard=False):
        conn = Conn(self.db_name)
        params = (self.symbol, self.exchange, interval, start_timestamp, finish_timestamp)
        if self.trade_type == TRADE_TYPE_FUTURE:
            params = (self.symbol, self.exchange, self.contract_type, interval, start_timestamp, finish_timestamp)

        candles = conn.query(self.sql, params)
        if standard:
            std_candles = []
            while candles:
                raw_candle = candles.pop(0)
                std_candles.append(self.__standard_candle(raw_candle))
            return std_candles

        return candles

    def range_query(self, start_timestamp, finish_timestamp, interval, standard=False):
        conn = Conn(self.db_name)
        params = (self.symbol, self.exchange, interval, start_timestamp, finish_timestamp)
        if self.trade_type == TRADE_TYPE_FUTURE:
            params = (self.symbol, self.exchange, self.contract_type, interval, start_timestamp, finish_timestamp)

        candles = conn.query(self.sql, params)
        conn.close()  # 手动关闭链接。
        for candle in candles:
            yield self.__standard_candle(candle) if standard else candle
        if len(candles) == 100:
            yield from self.range_query(candles[-1]["timestamp"] + 1000, finish_timestamp, interval, standard=standard)

    def range_query_1(self, start_timestamp, finish_timestamp, interval, standard=False, due_timestamp=0):
        conn = Conn(self.db_name)
        params = (start_timestamp, finish_timestamp, self.symbol, self.exchange, interval)
        candles = conn.query(
            "SELECT * FROM {} WHERE timestamp >= ? AND timestamp < ? AND symbol = ? AND exchange = ?"
            " AND `interval` = ? ORDER BY timestamp, due_timestamp LIMIT 100".format(self.table_name),
            params,
        )

        if due_timestamp:
            tmp_candles = conn.query(
                "SELECT * FROM {} WHERE timestamp = ? AND symbol = ? AND exchange = ? AND `interval` = ?"
                " AND due_timestamp > ?".format(self.table_name),
                (start_timestamp, self.symbol, self.exchange, interval, due_timestamp)
            )
            candles = tmp_candles + candles
        conn.close()  # 手动关闭链接。
        for candle in candles:
            yield self.__standard_candle(candle) if standard else candle
        if len(candles) >= 100:
            yield from self.range_query_1(
                candles[-1]["timestamp"] + 1000,
                finish_timestamp,
                interval,
                standard=standard,
                due_timestamp=candles[-1]["due_timestamp"],
            )
