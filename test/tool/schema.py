import unittest

from jsonschema import validate
from pyghostbt.tool.schema import *


class TestToolSchema(unittest.TestCase):
    def test_future_kline_input(self):
        instance = {
            "symbol": "btc_usd",
            "exchange": "okex",
            "contract_type": "quarter",
            "trade_type": "future",
            "db_name": "test",
        }
        validate(instance=instance, schema=future_kline_input)
