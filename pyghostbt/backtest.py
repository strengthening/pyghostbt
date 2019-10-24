from pyghostbt.tool.runtime import BacktestRuntime


class Backtest(BacktestRuntime):

    def back_test_wait_open(self):
        pass

    def back_test_opening(self):
        pass

    def back_test_wait_liquidate(self, timestamp):
        pass

    def back_test_liquidating(self, timestamp):
        pass
