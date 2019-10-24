import unittest

from pyghostbt.tool.param import *
from pyghostbt.const import *

config = {
    "instance_id": 1,
    "trade_type": TRADE_TYPE_FUTURE,
    "mode": MODE_BACKTEST,
    "db_name": "test",
    PARAM_NAME_POSITION: 1.1,
    PARAM_NAME_MAX_ABS_LOSS: -0.05
}


class TestToolParams(unittest.TestCase):
    # def test_save(self):
    #     p = Param(**config)
    #     p.save()

    def test_load(self):
        p = Param(**{
            "instance_id": 1,
            "trade_type": TRADE_TYPE_FUTURE,
            "mode": MODE_BACKTEST,
            "db_name": "test",
        })
        print(p.load())
