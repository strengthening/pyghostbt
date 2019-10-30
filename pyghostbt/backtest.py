from pyghostbt.util import uuid
from pyghostbt.strategy import Strategy


class Backtest(Strategy):
    def __init__(self, kw):
        super().__init__(kw)
        self.__setitem__("backtest_id", uuid())

    def back_test_wait_open(self):
        pass

    def back_test_opening(self):
        pass

    def back_test_wait_liquidate(self, timestamp):
        pass

    def back_test_liquidating(self, timestamp):
        pass
