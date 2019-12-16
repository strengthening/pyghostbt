from jsonschema import validate
from pyanalysis.mysql import Conn
from pyanalysis.moment import moment
from pyghostbt.const import *
from pyghostbt.util import real_number

order_input = {
    "type": "object",
    "required": ["symbol", "exchange", "instance_id", "sequence"],
    "properties": {
        "symbol": {
            "type": "string",
        },
        "exchange": {
            "type": "string",
        },
        "instance_id": {
            "type": "integer",
        },
        "sequence": {
            "type": "integer",
            "minimum": 0,
        },
        "backtest_id": {
            "type": "string",
            "minLength": 32,
            "maxLength": 32,
        },
    }
}

order_config = {
    "type": "object",
    "required": ["trade_type", "db_name", "mode"],
    "properties": {
        "trade_type": {
            "type": "string",
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT]
        },
        "db_name": {
            "type": "string", "minLength": 1
        },
        "mode": {
            "type": "string",
            "enum": [MODE_ONLINE, MODE_OFFLINE, MODE_BACKTEST],
        }
    }
}


class Order(dict):
    __TABLE_NAME_FORMAT__ = "{trade_type}_order_{mode}"

    def __init__(self, order, **kwargs):
        validate(instance=order, schema=order_input)
        validate(instance=kwargs, schema=order_config)
        super().__init__(order)

        self._trade_type = kwargs.get("trade_type")
        self._mode = kwargs.get("mode")
        self._db_name = kwargs.get("db_name")
        self._table_name = self.__TABLE_NAME_FORMAT__.format(**kwargs)


future_order_init = {
    "type": "object",
    "required": [
        "contract_type", "place_type", "price", "amount", "lever", "unit_amount",
    ],
    "properties": {
        "contract_type": {
            "type": "string",
            "enum": [
                CONTRACT_TYPE_THIS_WEEK,
                CONTRACT_TYPE_NEXT_WEEK,
                CONTRACT_TYPE_QUARTER,
            ],
        },
        "place_type": {
            "type": "string",
            "enum": [
                ORDER_PLACE_TYPE_T_MAKER,
                ORDER_PLACE_TYPE_B_MAKER,
                ORDER_PLACE_TYPE_T_TAKER,
                ORDER_PLACE_TYPE_B_TAKER,
                ORDER_PLACE_TYPE_O_SWAP,
                ORDER_PLACE_TYPE_L_SWAP,
                ORDER_PLACE_TYPE_MARKET,
            ],
        },
        "price": {
            "type": "integer",
        },
        "amount": {
            "type": "integer",
        },
        "lever": {
            "type": "integer",
        },
        "unit_amount": {
            "type": "integer",
        }
    }
}

# 保存到额时候说明在回测，所以需要更加严格的验证。
future_order_save = {
    "type": "object",
    "required": [
        "avg_price", "deal_amount", "fee", "place_timestamp", "place_datetime",
        "deal_timestamp", "deal_datetime", "due_timestamp", "due_datetime",
        "swap_timestamp", "swap_datetime", "cancel_timestamp", "cancel_datetime",
    ],
    "properties": {
        # "mode": {
        #     "type": "string",
        #     "enum": [MODE_BACKTEST],
        # },
        "avg_price": {
            "type": "integer",
        },
        "deal_amount": {
            "type": "integer",
        },
        "fee": {
            "type": "number",
        },
        "place_timestamp": {
            "type": "integer",
        },
        "place_datetime": {
            "type": "string",
        },
        "deal_timestamp": {
            "type": "integer",
        },
        "deal_datetime": {
            "type": "string",
        },
        "due_timestamp": {
            "type": "integer",
        },
        "due_datetime": {
            "type": "string",
        },
        "swap_timestamp": {
            "type": ["integer", "null"],
        },
        "swap_datetime": {
            "type": ["string", "null"],
        },
        "cancel_timestamp": {
            "type": ["integer", "null"],
        },
        "cancel_datetime": {
            "type": ["string", "null"],
        }
    }
}


class FutureOrder(Order):
    def __init__(self, order, **kwargs):
        super().__init__(order, **kwargs)
        validate(
            instance=order,
            schema=future_order_init,
        )
        self["fee"] = order.get("fee") or 0.0
        self["swap_timestamp"] = order.get("swap_timestamp") or 0
        self["swap_datetime"] = order.get("swap_datetime")
        self["cancel_timestamp"] = order.get("cancel_timestamp") or 0
        self["cancel_datetime"] = order.get("cancel_datetime")

    # 假设已经成交
    def deal(self, slippage=0.01, fee=-0.0005):
        # 回测时假设已经成交。
        self["deal_amount"] = self["amount"]
        self["status"] = 1
        if self["place_type"] in (ORDER_PLACE_TYPE_L_SWAP, ORDER_PLACE_TYPE_O_SWAP):
            slippage = 0.0
        if self["type"] == ORDER_TYPE_OPEN_LONG or self["type"] == ORDER_TYPE_LIQUIDATE_SHORT:
            self["avg_price"] = int(self["price"] * (1 + slippage))
            self["fee"] = self["amount"] * self["unit_amount"] * fee * 100000000 / self["avg_price"]
        elif self["type"] == ORDER_TYPE_OPEN_SHORT or self["type"] == ORDER_TYPE_LIQUIDATE_LONG:
            self["avg_price"] = int(self["price"] * (1 - slippage))
            self["fee"] = self["amount"] * self["unit_amount"] * fee * 100000000 / self["avg_price"]
        else:
            raise RuntimeError("error order type")

    def save(self, check: bool = False, raw_order_data: str = None, raw_market_data: str = None):
        if check:
            # 检验参数可用性
            validate(instance=self, schema=future_order_init)
            validate(instance=self, schema=future_order_save)

        conn = Conn(self._db_name)
        one = conn.query_one(
            "SELECT id FROM {} WHERE instance_id = ? AND sequence = ?".format(self._table_name),
            (self["instance_id"], self["sequence"]),
        )

        if one:
            conn.execute(
                "UPDATE {} SET place_type = ?, `type` = ?, price = ?, amount = ?,"
                " avg_price = ?, deal_amount = ?, status = ?, lever = ?, fee = ?,"
                " symbol = ?, exchange = ?, contract_type = ?, unit_amount = ?, "
                " place_timestamp = ?, place_datetime = ?, deal_timestamp = ?, deal_datetime = ?,"
                " due_timestamp = ?, due_datetime = ?, swap_timestamp = ?, swap_datetime = ?,"
                " cancel_timestamp = ?, cancel_datetime = ?, raw_order_data = ?, raw_market_data = ?"
                " WHERE instance_id = ? AND sequence = ?".format(self._table_name),
                (
                    self["place_type"], self["type"], self["price"], self["amount"],
                    self["avg_price"], self["deal_amount"], self["status"], self["lever"], self["fee"],
                    self["symbol"], self["exchange"], self["contract_type"], self["unit_amount"],
                    self["place_timestamp"], self["place_datetime"], self["deal_timestamp"], self["deal_datetime"],
                    self["due_timestamp"], self["due_datetime"], self["swap_timestamp"], self["swap_datetime"],
                    self["cancel_timestamp"], self["cancel_datetime"], raw_order_data, raw_market_data,
                    self["instance_id"], self["sequence"],
                ),
            )
        else:
            conn.insert(
                "INSERT INTO {} (instance_id, sequence, place_type, `type`, price,"
                " amount, avg_price, deal_amount, status, lever,"
                " fee, symbol, exchange, contract_type, unit_amount,"
                " place_timestamp, place_datetime, deal_timestamp, deal_datetime,"
                " due_timestamp, due_datetime, swap_timestamp, swap_datetime,"
                " cancel_timestamp, cancel_datetime, raw_order_data, raw_market_data) VALUES"
                " (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(
                    self._table_name,
                ),
                (
                    self["instance_id"], self["sequence"], self["place_type"], self["type"], self["price"],
                    self["amount"], self["avg_price"], self["deal_amount"], self["status"], self["lever"],
                    self["fee"], self["symbol"], self["exchange"], self["contract_type"], self["unit_amount"],
                    self["place_timestamp"], self["place_datetime"], self["deal_timestamp"], self["deal_datetime"],
                    self["due_timestamp"], self["due_datetime"], self["swap_timestamp"], self["swap_datetime"],
                    self["cancel_timestamp"], self["cancel_datetime"], raw_order_data, raw_market_data,
                ),
            )
        self.__update_instance()

    def __update_instance(self):
        conn = Conn(self._db_name)
        orders = conn.query(
            "SELECT * FROM {} WHERE instance_id = ? ORDER BY sequence".format(self._table_name),
            (self["instance_id"],),
        )

        open_times, open_amount, open_fee = 0, 0, 0.0
        open_start_timestamp, open_finish_timestamp = 0, 0
        open_start_datetime, open_finish_datetime = "", ""
        open_type, open_place_type = ORDER_TYPE_OPEN_LONG, ""

        liquidate_times, liquidate_amount, liquidate_fee = 0, 0, 0.0
        liquidate_start_timestamp, liquidate_finish_timestamp = 0, 0
        liquidate_start_datetime, liquidate_finish_datetime = "", ""
        liquidate_type, liquidate_place_type = ORDER_TYPE_LIQUIDATE_LONG, ""

        swap_times, swap_fee, swap_pnl_asset = 0, 0.0, 0
        swap_contract = {
            "open_amount": 0,
            "open_sum": 0,
            "open_avg_price": 0,
            "liquidate_sum": 0,
            "liquidate_amount": 0,
            "liquidate_avg_price": 0,
        }

        for order in orders:
            place_timestamp = order["place_timestamp"]
            place_datetime = moment.get(order["place_timestamp"]).to("Asia/Shanghai").format("YYYY-MM-DD HH:mm:ss")

            if order["type"] in (
                    ORDER_TYPE_OPEN_LONG,
                    ORDER_TYPE_OPEN_SHORT,
            ) and order["place_type"] not in (
                    ORDER_PLACE_TYPE_L_SWAP,
                    ORDER_PLACE_TYPE_O_SWAP,
            ):
                open_times += 1
                open_amount += order["deal_amount"]
                open_fee += order["fee"]
                open_type = order["type"]
                open_place_type = order["place_type"]

                if open_start_timestamp == 0:
                    open_start_timestamp = place_timestamp
                    open_start_datetime = place_datetime
                open_finish_timestamp = place_timestamp
                open_finish_datetime = place_datetime

            if order["type"] in (
                    ORDER_TYPE_LIQUIDATE_LONG,
                    ORDER_TYPE_LIQUIDATE_SHORT,
            ) and order["place_type"] not in (
                    ORDER_PLACE_TYPE_L_SWAP,
                    ORDER_PLACE_TYPE_O_SWAP,
            ):
                liquidate_times += 1
                liquidate_amount += order["deal_amount"]
                liquidate_fee += order["fee"]
                liquidate_type = order["type"]
                liquidate_place_type = order["place_type"]

                if liquidate_start_timestamp == 0:
                    liquidate_start_timestamp = place_timestamp
                    liquidate_start_datetime = place_datetime
                liquidate_finish_timestamp = place_timestamp
                liquidate_finish_datetime = place_datetime

            if order["place_type"] in (
                    ORDER_PLACE_TYPE_O_SWAP,
                    ORDER_PLACE_TYPE_L_SWAP,
            ):
                swap_fee += order["fee"]
                if order["type"] == ORDER_TYPE_OPEN_LONG:
                    swap_times += 1

                    swap_contract["open_amount"] += order["deal_amount"]
                    swap_contract["open_sum"] -= order["deal_amount"] * order["avg_price"]
                    swap_contract["open_avg_price"] = int(-swap_contract["open_sum"] / swap_contract["open_amount"])
                elif order["type"] == ORDER_TYPE_OPEN_SHORT:
                    swap_times += 1

                    swap_contract["open_amount"] += order["deal_amount"]
                    swap_contract["open_sum"] += order["deal_amount"] * order["avg_price"]
                    swap_contract["open_avg_price"] = int(swap_contract["open_sum"] / swap_contract["open_amount"])
                elif order["type"] == ORDER_TYPE_LIQUIDATE_LONG:
                    swap_contract["liquidate_amount"] += order["deal_amount"]
                    swap_contract["liquidate_sum"] += order["deal_amount"] * order["avg_price"]
                    swap_contract["liquidate_avg_price"] = int(
                        swap_contract["liquidate_sum"] / swap_contract["liquidate_amount"]
                    )
                elif order["type"] == ORDER_TYPE_LIQUIDATE_SHORT:
                    swap_contract["liquidate_amount"] += order["deal_amount"]
                    swap_contract["liquidate_sum"] -= order["deal_amount"] * order["avg_price"]
                    swap_contract["liquidate_avg_price"] = int(
                        -swap_contract["liquidate_sum"] / swap_contract["liquidate_amount"]
                    )
                else:
                    raise RuntimeError("can deal with the order type. ")

        if open_amount != liquidate_amount:
            return
        # 不需要计算swap的情况。
        if swap_contract["open_amount"] != swap_contract["liquidate_amount"]:
            return
        if swap_contract["open_amount"]:
            swap_pnl_asset = (swap_contract["open_sum"] + swap_contract["liquidate_sum"]) * self["unit_amount"]
            swap_pnl_asset = real_number(swap_pnl_asset)
            swap_pnl_asset /= real_number(swap_contract["open_avg_price"])
            swap_pnl_asset /= real_number(swap_contract["liquidate_avg_price"])

        conn.execute(
            "UPDATE future_instance_backtest SET open_times = ?, open_fee = ?, open_type = ?, open_place_type = ?,"
            " open_start_timestamp = ?, open_start_datetime = ?, open_finish_timestamp = ?, open_finish_datetime = ?, "
            " liquidate_times = ?, liquidate_fee = ?, liquidate_type = ?, liquidate_place_type = ?,"
            " liquidate_start_timestamp = ?, liquidate_start_datetime = ?,"
            " liquidate_finish_timestamp = ?, liquidate_finish_datetime = ?,"
            " swap_times = ?, swap_fee = ?, swap_pnl_asset = ? WHERE id = ?",
            (
                open_times, open_fee, open_type, open_place_type,
                open_start_timestamp, open_start_datetime, open_finish_timestamp, open_finish_datetime,
                liquidate_times, liquidate_fee, liquidate_type, liquidate_place_type,
                liquidate_start_timestamp, liquidate_start_datetime,
                liquidate_finish_timestamp, liquidate_finish_datetime,
                swap_times, swap_fee, swap_pnl_asset, self["instance_id"],
            ),
        )


class SwapOrder(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SpotOrder(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MarginOrder(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
