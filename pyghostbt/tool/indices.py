import talib
import numpy as np


class Indices(object):
    @staticmethod
    def EMA(close, time_period=30):
        if isinstance(close, list):
            close = np.array(close)
        return talib.EMA(close, time_period)

    @staticmethod
    def MACD(close, fast_period=12, slow_period=26, signal_period=9):
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
    def ATR(candles, time_period=14):
        return talib.ATR(
            np.array([k["high"] for k in candles]),
            np.array([k["low"] for k in candles]),
            np.array([k["close"] for k in candles]),
            time_period,
        )
