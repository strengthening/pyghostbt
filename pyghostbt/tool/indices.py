# 策略技术指标
import talib
import numpy as np

from jsonschema import validate
from typing import List
from pyanalysis.mysql import Conn
from pyghostbt.const import *

# 在此处设置对应的指标名称常量名称
# 真实波动幅度，
INDICES_NAME_ATR = "atr"

indices_input = {
    "type": "object",
    "properties": {
        INDICES_NAME_ATR: {"type": "number", "minimum": 0, "maximum": 100000000}
    }
}

indices_config = {
    "type": "object",
    "required": ["trade_type", "db_name", "mode"],
    "properties": {
        "trade_type": {
            "type": "string",
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT]
        },
        "db_name": {
            "type": "string", "minLength": 1
        },
        "mode": {
            "type": "string",
            "enum": [MODE_ONLINE, MODE_OFFLINE, MODE_BACKTEST, MODE_STRATEGY],
        },
        # "backtest_id": {
        #     "type": "string",
        #     "minLength": 32,
        #     "maxLength": 32
        # },
    }
}


class Indices(dict):
    __TABLE_NAME_FORMAT__ = "{trade_type}_indices_{mode}"

    def __init__(self, indices, **kwargs):
        validate(instance=indices, schema=indices_input)
        validate(instance=kwargs, schema=indices_config)
        super().__init__(indices)

        self._db_name = kwargs.get("db_name")
        self._mode = kwargs.get("mode")
        self._trade_type = kwargs.get("trade_type")
        self._table_name = self.__TABLE_NAME_FORMAT__.format(
            trade_type=self._trade_type,
            mode=MODE_BACKTEST if self._mode == MODE_BACKTEST else MODE_STRATEGY,
        )

    @staticmethod
    def SMA(
            closes: List[float],
            time_period: int = 30,
    ):
        closes = np.array([float(close) for close in closes])
        return [float(sma) for sma in talib.SMA(closes, time_period)]

    @staticmethod
    def EMA(
            closes: List[float],
            time_period: int = 30,
    ):
        closes = np.array([float(close) for close in closes])
        return [float(ema) for ema in talib.EMA(closes, time_period)]

    @staticmethod
    def MACD(
            close: List[float],
            fast_period: int = 12,
            slow_period: int = 26,
            signal_period: int = 9,
    ):
        if isinstance(close, list):
            close = np.array(close)
        return talib.MACD(close, fast_period, slow_period, signal_period)

    @staticmethod
    def FORCE(candles):
        result = np.array([])
        for i in range(len(candles)):
            if i == 0:
                result = np.append(result, np.nan)
            else:
                result = np.append(result, (candles[i]["close"] - candles[i - 1]["close"]) * candles[i]["vol"])
        return result

    @staticmethod
    def ATR(
            candles: List[dict],
            time_period: int = 14,
    ):
        # the return type is numpy.float64, so change it to pythons float
        return [float(atr) for atr in talib.ATR(
            np.array([float(k["high"]) for k in candles]),
            np.array([float(k["low"]) for k in candles]),
            np.array([float(k["close"]) for k in candles]),
            time_period,
        )]

    @staticmethod
    def DT_RANGE(candles: List[dict]):
        return max(
            max([c["high"] for c in candles]) - min([c["close"] for c in candles]),
            max([c["close"] for c in candles]) - min([c["low"] for c in candles]),
        )

    def add_item(self, indices):
        validate(instance=indices, schema=indices_input)
        for indices_name in indices:
            self[indices_name] = indices[indices_name]

    def load(self, instance_id):
        conn = Conn(self._db_name)
        results = conn.query(
            "SELECT * FROM {} WHERE instance_id = ?".format(self._table_name),
            (instance_id,),
        )
        for result in results:
            if result["indices_type"] == INDICES_TYPE_INTEGER:
                self[result["indices_name"]] = int(result["indices_value"])
            elif result["indices_type"] == INDICES_TYPE_FLOAT:
                self[result["indices_name"]] = float(result["indices_value"])
            else:
                self[result["indices_name"]] = result["indices_value"]

    def save(self, instance_id):
        if self._mode != MODE_BACKTEST:
            raise RuntimeError("You only can save data in backtest mode")
        # 入库前保证属性没有被篡改
        validate(instance=self, schema=indices_input)

        for name in self:
            if isinstance(self[name], int):
                sql_param = (PARAM_TYPE_INTEGER, str(self[name]), instance_id, name)
            elif isinstance(self[name], float):
                sql_param = (PARAM_TYPE_FLOAT, str(self[name]), instance_id, name)
            else:
                sql_param = (PARAM_TYPE_STRING, self[name], instance_id, name)

            conn = Conn(self._db_name)
            one = conn.query_one(
                "SELECT * FROM {} WHERE instance_id = ? AND indices_name = ?".format(self._table_name),
                (instance_id, name)
            )
            if one:
                conn.execute(
                    "UPDATE {} SET indices_type = ?, indices_value = ?"
                    " WHERE instance_id = ? AND indices_name = ?".format(self._table_name),
                    sql_param,
                )
            else:
                conn.insert(
                    "INSERT INTO {} (indices_type, indices_value, instance_id, indices_name)"
                    " VALUES (?, ?, ?, ?)".format(self._table_name),
                    sql_param,
                )
