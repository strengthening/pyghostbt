from pyghostbt.future.models import *

from pyexchange.okex.utils import get_the_due


class BackTest(Instance):
    def __init__(self, instance):
        super().__init__(instance)

    # 评价开仓策略 一段时间内的最大收益，最大回撤比例
    def analysis_open_instance(self):
        pass

    # 评价平仓策略 一段时间内的最大收益，最大回撤比例
    def analysis_liquidate_instance(self):
        pass

    # 回测专用判断wait instance是否被触发
    def back_test_open_instances(self, wait_instances):
        conn = Conn(self._get_db_name())
        open_instance = None
        order_type = ""

        for wait_instance in wait_instances:
            if order_type == "":
                order_type = wait_instance["order"]["type"]
            else:
                if order_type != wait_instance["order"]["type"]:
                    # 如果wait instances 交易类型不一样，则无法进行回测
                    raise ValueError("order type not same")
            order_direction = wait_instance["order"]["direction"]

            sql_fragment = "high > %s"
            if order_type == "open_long" and order_direction == "left":
                sql_fragment = "low < %s"
            if order_type == "open_short" and order_direction == "right":
                sql_fragment = "low < %s"

            query_sql = """SELECT * FROM {} WHERE symbol = %s AND exchange = %s AND
                     contract_type = %s AND timestamp >= %s AND timestamp < %s AND {}
                     ORDER BY timestamp LIMIT 1""".format(self._get_table_name(), sql_fragment)
            open_kline = conn.query_one(
                query_sql,
                (
                    self._symbol,
                    self._exchange,
                    self._contract_type,
                    wait_instance["order"]["start_timestamp"],
                    wait_instance["order"]["end_timestamp"],
                    wait_instance["order"]["open_price"],
                ),
            )

            if open_kline:
                wait_instance["order"]["open_date"] = open_kline["date"]
                wait_instance["order"]["open_timestamp"] = open_kline["timestamp"]
                wait_instance["order"]["open_price_avg"] = wait_instance["order"]["open_price"] * 1.005
                if order_type == "open_short":
                    wait_instance["order"]["open_price_avg"] = wait_instance["order"]["open_price"] * 0.995

                if order_direction == "left":
                    if order_type == "open_long":
                        wait_instance["order"]["open_price_avg"] = max(
                            wait_instance["order"]["open_price_avg"],
                            open_kline["low"] * 0.995,
                        )
                    else:
                        wait_instance["order"]["open_price_avg"] = min(
                            wait_instance["order"]["open_price_avg"],
                            open_kline["high"] * 1.005,
                        )

                wait_instance["order"]["risk_id"] = 0
                if open_instance is None or open_instance["order"]["open_timestamp"] > wait_instance["order"][
                    "open_timestamp"]:
                    open_instance = wait_instance

        if open_instance:
            order_future = open_instance["order"]
            due = get_the_due(self._contract_type, order_future["open_timestamp"])
            order_id = conn.insert(
                """INSERT INTO order_future (symbol, exchange, `type`, status, direction, position, 
                 strategy, unit_amount, due_timestamp, due_date, open_contract_type, open_price, open_price_avg,
                 open_timestamp, open_date, start_timestamp, end_timestamp, degree)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    self._symbol,
                    self._exchange,
                    order_future["type"],
                    "open",
                    order_future["direction"],
                    order_future["position"],
                    order_future["strategy"],
                    order_future["unit_amount"],
                    int(time.mktime(due.timetuple()) * 1000),
                    due.strftime("%Y-%m-%d %H:%M:%S"),
                    self._contract_type,
                    order_future["open_price"],
                    order_future["open_price_avg"],
                    order_future["open_timestamp"],
                    order_future["open_date"],
                    order_future["start_timestamp"],
                    order_future["end_timestamp"],
                    order_future["degree"],
                )
            )

            tech_future = open_instance["tech"]
            conn.execute(
                """INSERT INTO tech_future 
                (order_id, open_atr_daily, open_atr_rate_daily, opening_fast_ema_weekly, opening_slow_ema_weekly)
                VALUES (%s, %s, %s, %s, %s) """,
                (
                    order_id,
                    tech_future["open_atr_daily"] if "open_atr_daily" in tech_future else None,
                    tech_future["open_atr_rate_daily"] if "open_atr_rate_daily" in tech_future else None,
                    tech_future["opening_fast_ema_weekly"] if "opening_fast_ema_weekly" in tech_future else None,
                    tech_future["opening_slow_ema_weekly"] if "opening_slow_ema_weekly" in tech_future else None,
                )
            )

            param_future = Param(self._instance)
            param_future.sync(order_id)
        return open_instance

    # 回测专用判断 bottom top instance是否被触发
    def back_test_liquidate_instances(self, liquidate_instances):
        if self._instance["order"]["status"] != "open":
            raise ValueError("back_test instance order status is not open!")

        conn = Conn(self._get_db_name())
        order_future = self._instance["order"]
        start_timestamp = order_future["open_timestamp"] + 60 * 1000
        liquidate_kline = None
        liquidate_instance = None

        for instance in liquidate_instances:
            if order_future["status"] == "bottom":
                query_sql = """
                SELECT * FROM {} WHERE timestamp >= %s AND timestamp < %s AND due_timestamp = %s
                AND low < %s ORDER BY timestamp LIMIT 1
                """.format(self._get_table_name())
            else:
                query_sql = """
                SELECT * FROM {} WHERE timestamp >= %s AND timestamp < %s AND due_timestamp = %s
                AND high > %s ORDER BY timestamp LIMIT 1
                """.format(self._get_table_name())
            liquidate_kline = conn.query_one(
                query_sql,
                (
                    start_timestamp,
                    instance["order"]["due_timestamp"],
                    instance["order"]["due_timestamp"],
                    instance["order"]["liquidate_price"],
                )
            )
            if liquidate_kline:
                if liquidate_kline is None or liquidate_instance["timestamp"] > liquidate_kline["timestamp"]:
                    liquidate_kline = liquidate_kline
                    liquidate_instance = instance
                    liquidate_instance["order"]["liquidate_timestamp"] = liquidate_kline["timestamp"]
                    liquidate_instance["order"]["liquidate_date"] = liquidate_kline["date"]

        if liquidate_instance:
            conn.execute(
                """UPDATE order_future SET status = %s, liquidate_price = %s, liquidate_price_avg = %s,
                 liquidate_timestamp = %s, liquidate_date = %s, liquidate_contract_type = %s
                 WHERE symbol = %s AND exchange =%s AND open_contract_type = %s AND strategy = %s 
                 AND risk_id = %s AND start_timestamp = %s""",
                (
                    "liquidate",
                    liquidate_instance["order"]["liquidate_price"],
                    liquidate_instance["order"]["liquidate_price"] * 1.003,
                    liquidate_instance["order"]["liquidate_timestamp"],
                    liquidate_instance["order"]["liquidate_date"],
                    liquidate_instance["order"]["liquidate_contract_type"],
                    liquidate_instance["order"]["symbol"],
                    liquidate_instance["order"]["exchange"],
                    liquidate_instance["order"]["open_contract_type"],
                    liquidate_instance["order"]["strategy"],
                    liquidate_instance["order"]["risk_id"],
                    liquidate_instance["order"]["start_timestamp"],
                ),
            )

        return liquidate_instance
