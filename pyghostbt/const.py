BIRTHDAY_BTC = "2009-01-03 00:00:00"

MODE_STRATEGY = "strategy"
MODE_BACKTEST = "backtest"

KLINE_INTERVAL_1MIN = "1min"
KLINE_INTERVAL_15MIN = "15min"
KLINE_INTERVAL_1HOUR = "1hour"
KLINE_INTERVAL_4HOUR = "1hour"
KLINE_INTERVAL_1DAY = "1day"
KLINE_INTERVAL_1WEEK = "1week"

TRADE_TYPE_FUTURE = "future"
TRADE_TYPE_SWAP = "swap"
TRADE_TYPE_MARGIN = "margin"
TRADE_TYPE_SPOT = "spot"

EXCHANGE_OKEX = "okex"
EXCHANGE_HUOBI = "huobi"
EXCHANGE_BINANCE = "binance"

CONTRACT_TYPE_THIS_WEEK = "this_week"
CONTRACT_TYPE_NEXT_WEEK = "next_week"
CONTRACT_TYPE_QUARTER = "quarter"

PARAM_TYPE_STRING = "string"
PARAM_TYPE_INTEGER = "integer"
PARAM_TYPE_FLOAT = "float"

INDICES_INTERVAL_1MIN = "1min"
INDICES_INTERVAL_15MIN = "15min"
INDICES_INTERVAL_1HOUR = "1hour"
INDICES_INTERVAL_4HOUR = "1hour"
INDICES_INTERVAL_1DAY = "1day"
INDICES_INTERVAL_1WEEK = "1week"

INDICES_TYPE_STRING = "string"
INDICES_TYPE_INTEGER = "integer"
INDICES_TYPE_FLOAT = "float"

SUBJECT_INJECTION = "injection"  # 注资，为正
SUBJECT_DIVIDEND = "dividend"  # 分红，为负
SUBJECT_FREEZE = "freeze"  # 冻结，为负
SUBJECT_UNFREEZE = "unfreeze"  # 解冻，为正
SUBJECT_INCOME = "income"  # 收益，正负皆可
SUBJECT_TRANSACTION_FEE = "transaction_fee"  # 交易费用，为负
SUBJECT_LOAN_FEE = "loan_fee"  # 借贷费用，为负数
SUBJECT_ADJUSTMENT = "adjustment"  # 与交易所服务器进行校准，可为正可为负
SUBJECT_TRANSFER = "transfer"  # 内部转账，可为正可为负
