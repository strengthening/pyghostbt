from pyghostbt.future.models import *
from pyghostbt.future.strategy import Strategy


class BackTest(Strategy):
    def __init__(self, config):
        super().__init__(config)

    def analysis_open_instance(self):
        pass

    def analysis_liquidate_instance(self):
        pass

    def back_test_wait_open(self):
        pass

    def back_test_opening(self):
        pass
        # if self._instance["order"]["status"] != "open":
        #     raise ValueError("back_test instance order status is not open!")
        #
        # conn = Conn(self._get_db_name())
        # order_future = self._instance["order"]
        # start_timestamp = order_future["open_timestamp"] + 60 * 1000
        # liquidate_kline = None
        # liquidate_instance = None
        #
        # for instance in liquidate_instances:
        #     if order_future["status"] == "bottom":
        #         query_sql = """
        #         SELECT * FROM {} WHERE timestamp >= %s AND timestamp < %s AND due_timestamp = %s
        #         AND low < %s ORDER BY timestamp LIMIT 1
        #         """.format(self._get_table_name())
        #     else:
        #         query_sql = """
        #         SELECT * FROM {} WHERE timestamp >= %s AND timestamp < %s AND due_timestamp = %s
        #         AND high > %s ORDER BY timestamp LIMIT 1
        #         """.format(self._get_table_name())
        #     liquidate_kline = conn.query_one(
        #         query_sql,
        #         (
        #             start_timestamp,
        #             instance["order"]["due_timestamp"],
        #             instance["order"]["due_timestamp"],
        #             instance["order"]["liquidate_price"],
        #         )
        #     )
        #     if liquidate_kline:
        #         if liquidate_kline is None or liquidate_instance["timestamp"] > liquidate_kline["timestamp"]:
        #             liquidate_kline = liquidate_kline
        #             liquidate_instance = instance
        #             liquidate_instance["order"]["liquidate_timestamp"] = liquidate_kline["timestamp"]
        #             liquidate_instance["order"]["liquidate_date"] = liquidate_kline["date"]
        #
        # if liquidate_instance:
        #     conn.execute(
        #         """UPDATE order_future SET status = %s, liquidate_price = %s, liquidate_price_avg = %s,
        #          liquidate_timestamp = %s, liquidate_date = %s, liquidate_contract_type = %s
        #          WHERE symbol = %s AND exchange =%s AND open_contract_type = %s AND strategy = %s
        #          AND risk_id = %s AND start_timestamp = %s""",
        #         (
        #             "liquidate",
        #             liquidate_instance["order"]["liquidate_price"],
        #             liquidate_instance["order"]["liquidate_price"] * 1.003,
        #             liquidate_instance["order"]["liquidate_timestamp"],
        #             liquidate_instance["order"]["liquidate_date"],
        #             liquidate_instance["order"]["liquidate_contract_type"],
        #             liquidate_instance["order"]["symbol"],
        #             liquidate_instance["order"]["exchange"],
        #             liquidate_instance["order"]["open_contract_type"],
        #             liquidate_instance["order"]["strategy"],
        #             liquidate_instance["order"]["risk_id"],
        #             liquidate_instance["order"]["start_timestamp"],
        #         ),
        #     )
        #
        # return liquidate_instance

    # 回测专用判断wait instance是否被触发
    def back_test_wait_liquidate(self):
        pass
