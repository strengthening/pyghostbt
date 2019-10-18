from pyghostbt.const import *

kline_input = {
    "type": "object",
    "required": ["trade_type", "symbol", "exchange"],
    "properties": {
        "trade_type": {
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT],
        },
        "symbol": {"type": "string", "minLength": 1},
        "exchange": {
            "enum": [EXCHANGE_OKEX, EXCHANGE_HUOBI, EXCHANGE_BINANCE],
        },
        "contract_type": {
            "enum": [CONTRACT_TYPE_THIS_WEEK, CONTRACT_TYPE_NEXT_WEEK, CONTRACT_TYPE_QUARTER],
        },
        "db_name": {"type": "string", "minLength": 1},
    }
}
