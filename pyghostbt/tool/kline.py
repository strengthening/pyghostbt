from jsonschema import validate
from pyanalysis.mysql import Conn
from pyanalysis.moment import moment
from pyghostbt.util import standard_number
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
            "enum": [EXCHANGE_OKEX, EXCHANGE_HUOBI, EXCHANGE_BINANCE, EXCHANGE_BITSTAMP, EXCHANGE_COINBASE],
        },
        "contract_type": {
            "type": ["null", "string"],
            "enum": [None, CONTRACT_TYPE_THIS_WEEK, CONTRACT_TYPE_NEXT_WEEK, CONTRACT_TYPE_QUARTER, CONTRACT_TYPE_NONE],
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
    def __standard_candle(candle):
        candle["open"] = standard_number(candle["open"])
        candle["high"] = standard_number(candle["high"])
        candle["low"] = standard_number(candle["low"])
        candle["close"] = standard_number(candle["close"])
        return candle

    def query(
            self,
            start_timestamp: int,
            finish_timestamp: int,
            interval: str,
            standard: bool = False,
    ) -> list:
        candles = self.query_range(start_timestamp, finish_timestamp, interval, standard=standard)
        return [c for c in candles]

    def query_by_group(
            self,
            start_timestamp: int,
            finish_timestamp: int,
            interval: str,
            standard: bool = False,
    ):
        if interval == KLINE_INTERVAL_1MIN:
            return self.query(start_timestamp, finish_timestamp, interval, standard)

        intervals = {
            KLINE_INTERVAL_1DAY: 24 * 60 * 60 * 1000,
            KLINE_INTERVAL_4HOUR: 4 * 60 * 60 * 1000,
            KLINE_INTERVAL_1HOUR: 60 * 60 * 1000,
            KLINE_INTERVAL_15MIN: 15 * 60 * 1000,
        }

        if intervals.get(interval) is None:
            raise RuntimeError("can not use the interval", interval)

        num = intervals[interval]
        flag_timestamp = start_timestamp
        result = []

        while flag_timestamp < finish_timestamp:
            candles = self.query(flag_timestamp, flag_timestamp + num, KLINE_INTERVAL_1MIN, standard)
            flag_timestamp += num
            if len(candles) == 0:
                continue

            tmp_candle = candles[0].copy()
            tmp_candle["high"] = candles[0]["high"]
            tmp_candle["low"] = candles[0]["low"]
            tmp_candle["close"] = candles[-1]["close"]
            tmp_candle["vol"] = 0
            tmp_candle["timestamp"] = flag_timestamp
            tmp_candle["date"] = moment.get(flag_timestamp).to("Asia/Shanghai").format("YYYY-MM-DD HH:mm:ss")

            for candle in candles:
                if candle["high"] > tmp_candle["high"]:
                    tmp_candle["high"] = candle["high"]
                if candle["low"] < tmp_candle["low"]:
                    tmp_candle["low"] = candle["low"]
                tmp_candle["vol"] += candle["vol"]

            result.append(tmp_candle)
        return result

    def query_range(
            self,
            start_timestamp: int,
            finish_timestamp: int,
            interval: str,
            standard: bool = False
    ):
        conn = Conn(self.db_name)
        params = (self.symbol, self.exchange, interval, start_timestamp, finish_timestamp)
        if self.trade_type == TRADE_TYPE_FUTURE:
            params = (self.symbol, self.exchange, self.contract_type, interval, start_timestamp, finish_timestamp)

        candles = conn.query(self.sql, params)
        conn.close()  # 手动关闭链接。
        for candle in candles:
            yield self.__standard_candle(candle) if standard else candle
        if len(candles) == 100:
            yield from self.query_range(candles[-1]["timestamp"] + 1000, finish_timestamp, interval, standard=standard)

    def query_range_contracts(
            self,
            start_timestamp: int,
            finish_timestamp: int,
            interval: str,
            standard: bool = False,
            due_timestamp: int = 0,  # 辅助参数
    ):
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
                " AND due_timestamp > ? ORDER BY due_timestamp".format(self.table_name),
                (start_timestamp, self.symbol, self.exchange, interval, due_timestamp)
            )
            candles = tmp_candles + candles
        conn.close()  # 手动关闭链接。
        for candle in candles:
            yield self.__standard_candle(candle) if standard else candle
        if len(candles) >= 100:
            yield from self.query_range_contracts(
                candles[-1]["timestamp"] + 1000,
                finish_timestamp,
                interval,
                standard=standard,
                due_timestamp=candles[-1].get("due_timestamp") or 0,
            )
