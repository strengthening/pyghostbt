from pyghostbt.tool.runtime import Runtime


class Strategy(Runtime):
    def __init__(self, kw):
        super().__init__(kw)
        self._o = None

    def get_wait_open(self, timestamp):
        pass

    def get_opening(self, timestamp):
        pass

    def get_wait_liquidate(self, timestamp):
        pass

    def get_liquidating(self, timestamp):
        pass



