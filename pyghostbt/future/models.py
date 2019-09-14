import json
import os
import time
import datetime
import talib
import numpy as np

from pyanalysis.database.mysql import *


class Config(object):
    def __init__(self, config):
        self._config = config
        Config.__check(config)

    @staticmethod
    def __check(self, config):

        must_exist_keys = [

            "mode",
            "symbol",
            "exchange",
            "contract_type",
            "strategy",
            "unit_amount",
            "lever",
            "interval",

            "open_type",
            "open_place_type",
            "open_times",
            "open_swap",

            "liquidate_type",
            "liquidate_place_type",
            "liquidate_times",
            "liquidate_swap",

            "param_position",
            "param_abs_loss_ratio",
        ]

        for key in must_exist_keys:
            if key not in config:
                raise RuntimeError("Can not find the %s in the config" % key)

        if config["mode"] != "strategy" and config["mode"] != "backtest":
            raise ConfigValueError("mode", config["mode"])

    def get_param(self):
        param = {
            "position": self._config["param_position"],
            "abs_loss_ratio": self._config["param_abs_loss_ratio"],
        }
        return param



class ConfigValueError(Exception):
    def __init__(self, key, value):
        self._key = key
        self._value = value

    def __str__(self):
        return "The config %s can not be %s" % (self._key, self._value)


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


class Param(Instance):
    def __init__(self, instance):
        super().__init__(instance)
        self._param = self._instance["param"] if "param" in instance else None

    def list(self):
        params = []
        for key in self._param:
            if isinstance(self._param[key], int):
                params.append([key, "int", str(self._param[key])])
            elif isinstance(self._param[key], str):
                params.append([key, "string", str(self._param[key])])
            elif isinstance(self._param[key], float):
                params.append([key, "float", str(self._param[key])])
            else:
                pass
        return params

    def get(self, order_id):
        conn = Conn(self._get_db_name())
        params = conn.query("""SELECT * FROM order_future_param WHERE order_id = %s""", (order_id,))

        _params = {}
        for param in params:
            if param["type"] == "int":
                _params[param["name"]] = int(param["value"])
            elif param["type"] == "float":
                _params[param["name"]] = float(param["value"])
            else:
                _params[param["name"]] = param["value"]

        return _params

    def sync(self, order_id):
        param_future_sql = """INSERT INTO order_future_param (`order_id`, `name`, `type`, `value`) VALUES """
        params = self.list()
        if params:
            conn = Conn(self._get_db_name())
            param_future_sql += "(%s, %s, %s, %s), " * len(params)
            param_future_sql = param_future_sql[:-2]
            sql_params = ()
            for param in params:
                sql_params += (order_id, param[0], param[1], param[2])
            conn.execute(param_future_sql, sql_params)


#  获取k线数据的
class Kline(object):
    def __init__(self):
        super().__init__()

    def _get_by_interval(self, timestamp, data_period, interval, current=False):
        ts = Timestamp(timestamp)
        end_timestamp = ts.get_by_interval(interval)
        start_timestamp = end_timestamp - data_period * self._intervals[interval]
        kline_intervals = []

        for i in range(data_period):
            # if interval != "weekly":
            kline_day = self._get_kline(
                start_timestamp + i * self._intervals[interval],
                start_timestamp + (i + 1) * self._intervals[interval],
            )
            kline_intervals.append(kline_day)

        if current:
            kline_current = self._get_kline(end_timestamp, ts.get_the_minute())
            if kline_current["vol"] == 0:
                kline_current["open"], kline_current["high"] = kline_intervals[-1]["close"], kline_intervals[-1][
                    "close"]
                kline_current["low"], kline_current["close"] = kline_intervals[-1]["close"], kline_intervals[-1][
                    "close"]
            kline_intervals.append(kline_current)

        return kline_intervals

    def _get_kline(self, start_timestamp, end_timestamp):
        query_sql = """SELECT MAX(high) AS high, MIN(low) AS low, SUM(vol) AS vol FROM {} WHERE symbol=%s
         AND exchange=%s AND contract_type=%s AND timestamp >= %s AND timestamp < %s""".format(self._get_table_name())
        conn = Conn(self._get_db_name())
        result = conn.query_one(query_sql, (
            self._symbol,
            self._exchange,
            self._contract_type,
            start_timestamp,
            end_timestamp,
        ))
        if result["high"] is None or result["low"] is None or result["vol"] is None:
            query_sql = """SELECT close FROM {} WHERE symbol = %s AND exchange=%s AND contract_type=%s
             AND timestamp <= %s ORDER BY timestamp DESC LIMIT 1""".format(self._get_table_name())
            result = conn.query_one(query_sql, (
                self._symbol,
                self._exchange,
                self._contract_type,
                start_timestamp,
            ))
            result["close"] = float(result["close"])
            result["open"] = float(result["close"])
            result["high"] = float(result["close"])
            result["low"] = float(result["close"])
            result["vol"] = 0
            return result

        query_sql = """SELECT open FROM {} WHERE symbol=%s AND exchange=%s AND contract_type=%s
         AND timestamp >=%s AND timestamp <%s ORDER BY timestamp LIMIT 1""".format(self._get_table_name())
        open_result = conn.query_one(query_sql, (
            self._symbol,
            self._exchange,
            self._contract_type,
            start_timestamp,
            end_timestamp,
        ))
        result["open"] = float(open_result["open"])  # if open_result else

        query_sql = """SELECT close FROM {} WHERE symbol=%s AND exchange=%s AND contract_type=%s
         AND timestamp >= %s AND timestamp < %s ORDER BY timestamp DESC LIMIT 1""".format(self._get_table_name())
        close_result = conn.query_one(query_sql, (
            self._symbol,
            self._exchange,
            self._contract_type,
            start_timestamp,
            end_timestamp,
        ))
        result["close"] = float(close_result["close"])
        result["high"] = float(result["high"])
        result["low"] = float(result["low"])
        result["vol"] = float(result["vol"])
        result["timestamp"] = start_timestamp
        result["date"] = datetime.datetime.fromtimestamp(start_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        return result

    # 数据不足的情况下，去查找week表的数据
    def _get_weekly_kline(self, start_timestamp, end_timestamp):

        query_sql = """SELECT COUNT(1) AS num FROM {} WHERE symbol=%s
         AND exchange=%s AND contract_type=%s AND timestamp >= %s AND timestamp < %s""".format(self._get_table_name())
        conn = Conn(self._get_db_name())
        result = conn.query_one(query_sql, (
            self._symbol,
            self._exchange,
            self._contract_type,
            start_timestamp,
            end_timestamp,
        ))
        # 如果kline数量小于5000 则使用week数据
        if result["num"] <= 3000:
            query_week_sql = """SELECT * FROM {} WHERE symbol=%s 
                AND exchange=%s AND contract_type=%s AND timestamp=%s""".format(self._get_table_name(interval="weekly"))
            return conn.query_one(query_week_sql,
                                  (
                                      self._symbol,
                                      self._exchange,
                                      self._contract_type,
                                      start_timestamp
                                  ))
        return self._get_kline(start_timestamp, end_timestamp)

    def get_weekly(self, timestamp, data_period, current=False):
        return self._get_by_interval(timestamp, data_period, "weekly", current=current)

    def get_daily(self, timestamp, data_period, current=False):
        return self._get_by_interval(timestamp, data_period, "daily", current=current)

    def get_hourly(self, timestamp, data_period, current=False):
        return self._get_by_interval(timestamp, data_period, "hourly", current=current)

    def get_current_interval(self, timestamp, interval):
        ts = Timestamp(timestamp)
        start_timestamp = ts.get_by_interval(interval)
        return self._get_kline(start_timestamp, timestamp)


# class Timestamp(object):
#     def __init__(self, ts=None):
#         if ts:
#             self._ts = ts
#         else:
#             self._ts = int(time.time()) * 1000
#
#         self._intervals = {
#             "weekly": 7 * 24 * 60 * 60 * 1000,
#             "daily": 24 * 60 * 60 * 1000,
#             "hourly": 60 * 60 * 1000,
#             "minutely": 60 * 1000
#         }
#
#     def get_contract(self, due_timestamp, exchange="okex"):
#         if exchange != "okex":
#             raise ValueError("exchange is not okex")
#         minus_timestamp = due_timestamp - self._ts
#         if minus_timestamp <= 7 * 24 * 60 * 60 * 1000:
#             return "this_week"
#         elif (7 * 24 * 60 * 60 * 1000) < minus_timestamp <= (14 * 24 * 60 * 60 * 1000):
#             return "next_week"
#         else:
#             return "quarter"
#
#     def get_the_month(self):
#         the_datetime = datetime.datetime.fromtimestamp(self._ts / 1000)
#         the_month = datetime.datetime(the_datetime.year, the_datetime.month, 1, 0, 0, 0, 0)
#         # next_month = datetime.datetime(the_datetime.year, the_datetime.month + 1, 1, 0, 0, 0, 0)
#         return int(the_month.timestamp() * 1000)  # , int(next_month.timestamp() * 1000)
#
#     def get_the_week(self):
#         start_timestamp = 1262534400000  # 2010/1/4 00:00:00@ beijing 周一开始
#         weeks = int((self._ts - start_timestamp) / 1000 / 60 / 60 / 24 / 7)
#         return start_timestamp + weeks * 1000 * 60 * 60 * 24 * 7
#
#     def get_the_day(self):
#         start_timestamp = 1262275200000  # 2010/1/1 00:00:00@ beijing
#         days = int((self._ts - start_timestamp) / 1000 / 60 / 60 / 24)
#         return start_timestamp + days * 1000 * 60 * 60 * 24
#
#     def get_the_hour(self):
#         return int(self._ts / 1000 / 60 / 60) * 1000 * 60 * 60
#
#     def get_the_minute(self):
#         return int(self._ts / 1000 / 60) * 1000 * 60
#
#     def get_by_interval(self, interval):
#         interval_funcs = {
#             "weekly": self.get_the_week,
#             "daily": self.get_the_day,
#             "hourly": self.get_the_hour,
#             "minutely": self.get_the_minute
#         }
#         if interval in interval_funcs:
#             return interval_funcs[interval]()
#         return self._ts
#
#     def get_ms_by_interval(self, interval):
#         if interval in self._intervals:
#             return self._intervals[interval]
#         return 0
