import unittest

from pyghostbt.tool.param import *
from pyghostbt.const import *

config = {
    PARAM_NAME_POSITION: 1.1,
    PARAM_NAME_MAX_ABS_LOSS: -0.05
}


class TestToolParams(unittest.TestCase):
    # def test_save(self):
    #     p = Param(**config)
    #     p.save()

    def test_load(self):
        p = Param(
            config,
            instance_id=1,
            trade_type=TRADE_TYPE_FUTURE, mode=MODE_BACKTEST, db_name="test",
        )
        print(p)
        # p.save(1)
        p.load(1)
        print(p)

