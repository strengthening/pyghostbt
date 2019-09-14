from pyghostbt.future.models import *


class Strategy(Config):
    def __init__(self, config):
        super().__init__(config)
        self._T = Technology
        self._K = Kline

    def risk_control(self, timestamp):
        pass
        # conn = Conn(self._get_db_name())
        # # 同时开仓的订单
        # open_orders = conn.query(
        #     """SELECT id, start_timestamp FROM order_future
        #       WHERE symbol = %s AND exchange = %s AND open_contract_type = %s AND strategy = %s
        #       AND open_timestamp < %s AND (liquidate_timestamp IS NULL OR liquidate_timestamp > %s)
        #       ORDER BY open_timestamp
        #     """,
        #     (self._symbol, self._exchange, self._contract_type, self._strategy, timestamp, timestamp)
        # )
        #
        # if len(open_orders) >= 3:
        #     print("同时开仓超过3笔")
        #     return True
        #
        # # 已经成交，不生成对应的交易逻辑
        # conn = Conn(self._get_db_name())
        # orders = conn.query(
        #     """SELECT * FROM order_future WHERE symbol = %s AND exchange = %s AND open_contract_type = %s
        #      AND strategy = %s AND start_timestamp = %s""",
        #     (
        #         self._symbol,
        #         self._exchange,
        #         self._contract_type,
        #         self._strategy,
        #         Timestamp(timestamp).get_the_day()
        #     )
        # )
        # if orders:
        #     return True
        #
        # return False

    def get_wait_open(self, timestamp):
        pass

    def get_opening(self, timestamp):
        pass

    def get_wait_liquidate(self, timestamp):
        pass

    def get_liquidating(self, timestamp):
        pass