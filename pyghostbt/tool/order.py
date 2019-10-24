# 订单及下单手段的逻辑


class Order(object):
    def __init__(self, **kwargs):
        pass


class Open(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass


class Liquidate(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass


class Buy(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass


class Sell(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass
