# 订单及下单手段的逻辑

from jsonschema import validate
from pyghostbt.const import *

order_input = {
    "type": "object",
    "required": ["trade_type", "db_name", "mode", "symbol", "exchange", "instance_id", "sequence"],
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
        },
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
        },
        "backtest_id": {
            "type": "string",
            "minLength": 32,
            "maxLength": 32
        },
    }
}

future_order_input = {

    "type": "object",
    "required": ["contract_type", "place_type", "price", "amount", "lever"],
    "properties": {
        "place_type": {
            "type": "string",
            "enum": [ORDER_PLACE_TYPE_MAKER, ORDER_PLACE_TYPE_TAKER, ORDER_PLACE_TYPE_SWAPPER],
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
        "contract_type": {
            "type": "string",
            "enum": [CONTRACT_TYPE_THIS_WEEK, CONTRACT_TYPE_NEXT_WEEK, CONTRACT_TYPE_QUARTER],
        }
    }

}


class Order(dict):
    __TABLE_NAME_FORMAT__ = "{trade_type}_order_{mode}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        validate(instance=kwargs, schema=order_input)


class FutureOrder(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        validate(instance=kwargs, schema=future_order_input)


class SwapOrder(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SpotOrder(Order):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MarginOrder(Order):
    def __init__(self,  **kwargs):
        super().__init__(**kwargs)
