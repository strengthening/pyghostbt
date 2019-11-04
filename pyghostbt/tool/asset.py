from jsonschema import validate
from pyghostbt.const import *
from pyanalysis.mysql import Conn
from pyanalysis.moment import moment

asset_input = {
    "type": "object",
    "required": ["trade_type", "symbol", "exchange", "contract_type", "mode", "db_name"],
    "properties": {
        "trade_type": {
            "type": "string",
            "enum": [
                TRADE_TYPE_FUTURE,
                TRADE_TYPE_SWAP,
                TRADE_TYPE_MARGIN,
                TRADE_TYPE_SPOT,
            ],
        },
        "symbol": {
            "type": "string",
            "minLength": 1,
        },
        "exchange": {
            "type": "string",
            "enum": [
                EXCHANGE_OKEX,
                EXCHANGE_HUOBI,
                EXCHANGE_BINANCE,
            ],
        },
        "contract_type": {
            "type": "string",
            "enum": [
                CONTRACT_TYPE_THIS_WEEK,
                CONTRACT_TYPE_NEXT_WEEK,
                CONTRACT_TYPE_QUARTER,
            ],
        },
        "mode": {
            "type": "string",
            "enum": [
                MODE_ONLINE,
                MODE_ONLINE,
                MODE_BACKTEST,
            ],
        },
        "db_name": {
            "type": "string",
            "minLength": 1,
        },
        "backtest_id": {
            "type": "string",
            "minLength": 32,
            "maxLength": 32,
        }
    }
}

account_flow_input = {
    "type": "object",
    "required": ["subject", "amount", "position", "timestamp", "datetime"],
    "properties": {
        "subject": {
            "type": "string",
            "enum": [
                SUBJECT_INJECTION,
                SUBJECT_DIVIDEND,
                SUBJECT_FREEZE,
                SUBJECT_UNFREEZE,
                SUBJECT_INCOME,
                SUBJECT_TRANSACTION_FEE,
                SUBJECT_LOAN_FEE,
                SUBJECT_ADJUSTMENT,
                SUBJECT_TRANSFER,
            ],
        },
        "amount": {
            "type": "integer",
        },
        "position": {
            "type": "number",
        },
        "timestamp": {
            "type": "integer",
            "minimum": 1000000000000,
            "maximum": 9999999999999,
        }
    }
}


class Asset(dict):
    __ASSET_TABLE_NAME_FORMAT__ = "{trade_type}_asset_{mode}"
    __ACCOUNT_FLOW_TABLE_NAME_FORMAT__ = "{trade_type}_account_flow_{mode}"

    def __init__(self, **kwargs):
        super().__init__()
        validate(instance=kwargs, schema=asset_input)

        self._symbol = kwargs.get("symbol")
        self._exchange = kwargs.get("exchange")
        self._contract_type = kwargs.get("contract_type")
        self._trade_type = kwargs.get("trade_type")
        self._mode = kwargs.get("mode")
        self._backtest_id = kwargs.get("backtest_id")

        self.db_name = kwargs.get("db_name_asset") or kwargs.get("db_name")
        self._asset_table_name = self.__ASSET_TABLE_NAME_FORMAT__.format(
            trade_type=self._trade_type,
            mode=self._mode if self._mode == MODE_BACKTEST else "strategy",
        )
        self._account_flow_table_name = self.__ACCOUNT_FLOW_TABLE_NAME_FORMAT__.format(
            trade_type=self._trade_type,
            mode=self._mode if self._mode == MODE_BACKTEST else "strategy",
        )

    def __add_account_flow_item(self, **kwargs):
        """
        add record in account flow table
        :param
            subject: the item of account flow
            amount: the amount of flow, the real amount * 100000000
            position: the position of the flow
            timestamp: the item of account flow

        :return: None
        """

        if self._mode != MODE_BACKTEST:
            raise RuntimeError("Only backtest mode can insert data into table. ")
        validate(instance=kwargs, schema=account_flow_input)
        conn = Conn(self.db_name)
        conn.insert(
            """
            INSERT INTO {} (symbol, exchange, contract_type, backtest_id, subject, amount,
            position, timestamp, datetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """.format(self._account_flow_table_name),
            (
                self._symbol, self._exchange, self._contract_type, self._backtest_id,
                kwargs.get("subject"), int(kwargs.get("amount") * 100000000 + 0.5), kwargs.get("position"),
                kwargs.get("timestamp"), kwargs.get("datetime"),
            ),
        )

        position = conn.query_one(
            """SELECT SUM(position) AS position FROM {}
            WHERE symbol = ? AND exchange = ? AND backtest_id = ? AND timestamp <= ?
            """.format(self.account_flow_table_name),
            (self._symbol, self._exchange, self._backtest_id, kwargs.get("timestamp"))
        )["position"]

        amount = conn.query_one(
            """
            SELECT SUM(amount)/100000000 AS amount FROM {} 
            WHERE symbol = ? AND exchange = ? AND backtest_id = ? AND timestamp <= ?
            AND subject NOT IN (?, ?)
            """.format(self._account_flow_table_name),
            (
                self._symbol, self._exchange, self._backtest_id, kwargs.get("timestamp"),
                SUBJECT_FREEZE, SUBJECT_UNFREEZE,
            ),
        )["amount"]

        conn.insert(
            """
            INSERT INTO {} (symbol, exchange, backtest_id, total_asset, sub_asset, sub_freeze_asset, 
            total_position, sub_position, sub_freeze_position, timestamp, datetime) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """.format(self._asset_table_name),
            (
                self._symbol, self._exchange, self._backtest_id, amount, 0, 0, 0, 0, position,
                kwargs.get("timestamp"), kwargs.get("datetime"),
            )
        )

    # 回测是初始化账户，主要是注资
    def init_account(self, amount):
        m = moment.get(BIRTHDAY_BTC)
        self.__add_account_flow_item(
            subject=SUBJECT_INJECTION,
            amount=amount,
            position=0,
            timestamp=m.millisecond_timestamp,
            datetime=m.format("YYYY-MM-DD HH:mm:ss"),
        )

    def freeze(self, amount, position, timestamp):
        if amount >= 0 or position <= 0:
            raise RuntimeError("the freeze input param error")
        m = moment.get(timestamp)
        self.__add_account_flow_item(
            subject=SUBJECT_FREEZE,
            amount=amount,
            position=position,
            timestamp=timestamp,
            datetime=m.format("YYYY-MM-DD HH:mm:ss"),
        )

    def unfreeze(self, amount, position, timestamp):
        if amount <= 0 or position >= 0:
            raise RuntimeError("the unfreeze input param error")
        m = moment.get(timestamp)
        self.__add_account_flow_item(
            subject=SUBJECT_UNFREEZE,
            amount=amount,
            position=position,
            timestamp=timestamp,
            datetime=m.format("YYYY-MM-DD HH:mm:ss"),
        )

    def income(self, amount, timestamp):
        m = moment.get(timestamp)
        self.__add_account_flow_item(
            subject=SUBJECT_INCOME,
            amount=amount,
            position=0,
            timestamp=timestamp,
            datetime=m.format("YYYY-MM-DD HH:mm:ss"),
        )

    def load(self, timestamp):
        sql = """
        SELECT * FROM {} WHERE symbol = ? AND exchange = ? AND timestamp <= ? 
        ORDER BY timestamp DESC, id DESC LIMIT 1
        """.format(self._asset_table_name)
        params = (self._symbol, self._exchange, timestamp)

        if self._mode == MODE_BACKTEST:
            sql = """
            SELECT * FROM {} WHERE symbol = ? AND exchange = ? AND timestamp <= ? AND backtest_id = ?
            ORDER BY timestamp DESC, id DESC LIMIT 1
            """.format(self._asset_table_name)
            params = (self._symbol, self._exchange, timestamp, self._backtest_id)
        conn = Conn(self.db_name)
        result = conn.query_one(sql, params)
        self["total_asset"] = result["total_asset"]
        self["sub_asset"] = result["sub_asset"]
        self["sub_freeze_asset"] = result["sub_freeze_asset"]
        self["total_position"] = result["total_position"]
        self["sub_position"] = result["sub_position"]
        self["sub_freeze_position"] = result["sub_freeze_position"]
        return self
