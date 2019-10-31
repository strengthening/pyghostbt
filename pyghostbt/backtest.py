from pyghostbt.util import uuid


class Backtest(dict):
    def __init__(self, kw):
        super().__init__(kw)
        if not self.get("backtest_id"):
            self.__setitem__("backtest_id", uuid())

    def back_test_wait_open(self):
        pass

    def back_test_opening(self):
        pass

    def back_test_wait_liquidate(self, timestamp):
        pass

    def back_test_liquidating(self, timestamp):
        pass
