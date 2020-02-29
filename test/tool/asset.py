import unittest

from pyanalysis.moment import moment
from pyghostbt.util import uuid
from pyghostbt.tool.asset import Asset
from pyghostbt.const import MODE_BACKTEST
from pyghostbt.const import TRADE_TYPE_FUTURE


class TestAsset(unittest.TestCase):

    def test_ffreeze(self):
        backtest_id = uuid()
        asset = Asset(
            trade_type=TRADE_TYPE_FUTURE,
            symbol="btc_usd",
            exchange="okex",
            db_name="test",
            mode=MODE_BACKTEST,
            backtest_id=backtest_id,
        )

        asset.first_invest(20.0, 20.0, 10.0)
        asset.ffreeze(1, 1, moment.now("Asia/Shanghai").millisecond_timestamp)

