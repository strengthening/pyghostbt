import unittest

from pyghostbt.tool.klines import Kline
from pyghostbt.const import *

config = {
    "symbol": "btc_usd",
    "exchange": "okex",
    "contract_type": "quarter",
    "trade_type": "future",
    "db_name": "test",
}


class TestMarketKline(unittest.TestCase):
    def test_raw_query(self):
        k = Kline(**config)
        result = k.raw_query(1571180425000, 1571284025000, KLINE_INTERVAL_1MIN, standard=True)
        print(result)

    def test_range_query(self):
        k = Kline(**config)
        results = k.range_query(1571180425000, 1571284025000, KLINE_INTERVAL_1MIN, standard=True)

        i = 0
        for result in results:
            i += 1
            print(result)
            print(i)
