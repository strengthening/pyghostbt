# 策略配置

from pyghostbt.const import *

instance_input = {
    "type": "object",
    "required": ["trade_type", "db_name", "mode"],
    "properties": {
        "backtest_id": {
            "type": "string",
            "minLength": 32,
            "maxLength": 32
        },
        "trade_type": {
            "type": "string",
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT]
        },
        "db_name": {
            "type": "string", "minLength": 1
        },
        "mode": {
            "type": "string",
            "enum": [MODE_STRATEGY, MODE_BACKTEST],
        }
    }
}

class Instance(object):
    def __init__(self, **kwargs):
        super().__init__()

        pass
