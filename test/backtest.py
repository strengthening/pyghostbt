
strategy_1st_config = {
    "mode": "backtest",
    "symbol": "btc_usd",
    "exchange": "okex",
    "contract_type": "quarter",
    "trade_type": "future",
    "unit_amount": 100,
    "lever": 10,
    "interval": "1min",

    "db_name": "test",
    "db_name_kline": "ghost-etl",
    "timezone": "Asia/Shanghai",
    "param": {
        "position": 0.5,
        "max_abs_loss": 0.05,
    },
    "order": {}
}


# class
