from jsonschema import validate
from pyanalysis.mysql import Conn
from pyghostbt.const import *

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
        "contract_type", "place_type", "price", "amount", "lever",
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
        }
    }
}

# 保存到额时候说明在回测，所以需要更加严格的验证。
future_order_save = {
    "type": "object",
    "required": [
        "mode", "avg_price", "deal_amount", "fee", "place_timestamp", "place_datetime",
        "deal_timestamp", "deal_datetime", "due_timestamp", "due_datetime",
        "swap_timestamp", "swap_datetime", "cancel_timestamp", "cancel_datetime",
    ],
    "properties": {
        "mode": {
            "type": "string",
            "enum": [MODE_BACKTEST],
        },
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
        self["swap_date"] = order.get("swap_date")
        self["cancel_timestamp"] = order.get("cancel_timestamp") or 0
        self["cancel_date"] = order.get("cancel_date")

    # 假设已经成交
    def deal(self, slippage=0.01, fee=-0.0005):
        # 回测时假设已经成交。
        if self["type"] == ORDER_TYPE_OPEN_LONG or self["type"] == ORDER_TYPE_LIQUIDATE_SHORT:
            self["avg_price"] = int(self["price"] * (1 + slippage))
            self["deal_amount"] = self["amount"]
            self["fee"] = self["amount"] * self["unit_amount"] * fee * 100000000 / self["avg_price"]
        elif self["type"] == ORDER_TYPE_OPEN_SHORT or self["type"] == ORDER_TYPE_LIQUIDATE_LONG:
            self["avg_price"] = int(self["price"] * (1 - slippage))
            self["deal_amount"] = self["amount"]
            self["fee"] = self["amount"] * self["unit_amount"] * fee * 100000000 / self["avg_price"]
        else:
            raise RuntimeError("error order type")

    def save(self, check=False):
        if check:
            # 检验参数可用性
            validate(instance=self, schema=future_order_init)
            validate(instance=self, schema=future_order_save)
        conn = Conn(self._db_name)
        conn.insert(
            "INSERT INTO {} (instance_id, sequence, place_type, `type`, price, amount,"
            " avg_price, deal_amount, status, lever, fee, symbol, exchange, contract_type,"
            " place_timestamp, place_date, deal_timestamp, deal_date, due_timestamp,"
            " due_date, swap_timestamp, swap_date, cancel_timestamp, cancel_date)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)".format(self._table_name),
            (
                self["instance_id"], self["sequence"], self["place_type"], self["type"], self["price"], self["amount"],
                self["avg_price"], self["deal_amount"], self["status"], self["lever"], self["fee"], self["symbol"],
                self["exchange"], self["contract_type"], self["place_timestamp"], self["place_date"],
                self["deal_timestamp"], self["deal_date"], self["due_timestamp"], self["due_date"],
                self["swap_timestamp"], self["swap_date"], self["cancel_timestamp"], self["cancel_date"]
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
