import talib
import numpy as np

from pyanalysis.mysql import Conn


class Technology(object):
    @staticmethod
    def ema(close, timeperiod=30):
        if isinstance(close, list):
            close = np.array(close)
        return talib.EMA(close, timeperiod)

    @staticmethod
    def macd(close, fastperiod=12, slowperiod=26, signalperiod=9):
        if isinstance(close, list):
            close = np.array(close)
        return talib.MACD(close, fastperiod, slowperiod, signalperiod)

    @staticmethod
    def force(klines):
        result = np.array([])
        for i in range(len(klines)):
            if i == 0:
                result = np.append(result, np.nan)
            else:
                result = np.append(result, (klines[i]["close"] - klines[i - 1]["close"]) * klines[i]["vol"])
        return result

    @staticmethod
    def atr(klines, timeperiod=14):
        return talib.ATR(
            np.array([k["high"] for k in klines]),
            np.array([k["low"] for k in klines]),
            np.array([k["close"] for k in klines]), timeperiod)


class Indices(object):
    pass


#  获取k线数据的
class Kline(object):
    __TABLE_NAME_FORMAT__ = "{trade_type}_kline_{symbol}"

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.symbol = kwargs["symbol"] if "symbol" in kwargs else "btc_usd"
        self.exchange = kwargs["exchange"] if "exchange" in kwargs else "okex"
        self.contract_type = kwargs["contract_type"] if "contract_type" in kwargs else "quarter"
        self.trade_type = kwargs["trade_type"] if "trade_type" in kwargs else "future"

        self.db_name = kwargs["db_name"] if "db_name" in kwargs else "default"
        self.table_name = self.__TABLE_NAME_FORMAT__.format(
            trade_type=self.trade_type,
            symbol=self.symbol,
        )

    def raw_query(self, start_timestamp, finish_timestamp, interval):
        conn = Conn(self.db_name)
        candles = conn.query(
            "SELECT * FROM {} WHERE symbol = ? AND exchange = ? AND contract_type = ?"
            " AND `interval` = ? AND timestamp >= ? AND timestamp < ? "
            " ORDER BY timestamp".format(self.table_name),
            (
                self.symbol,
                self.exchange,
                self.contract_type,
                interval,
                start_timestamp,
                finish_timestamp,
            )
        )

        return candles

    def range_query(self, start_timestamp, finish_timestamp, interval):
        conn = Conn(self.db_name)
        candles = conn.query(
            "SELECT * FROM {} WHERE symbol = ? AND exchange = ? AND contract_type = ?"
            " AND `interval` = ? AND timestamp >= ? AND timestamp < ? "
            " ORDER BY timestamp LIMIT 100".format(self.table_name),
            (
                self.symbol,
                self.exchange,
                self.contract_type,
                interval,
                start_timestamp,
                finish_timestamp,
            )
        )

        for candle in candles:
            yield candle
        if len(candles) == 100:
            self.range_query(candles[-1]["timestamp"]+1000, finish_timestamp)
