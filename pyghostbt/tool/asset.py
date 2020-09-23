from jsonschema import validate
from pyghostbt.const import *
from pyghostbt.util import standard_number
from pyghostbt.util import real_number
from pyanalysis.mysql import Conn
from pyanalysis.moment import moment

asset_input = {
    "type": "object",
    "required": [
        "trade_type",
        "symbol",
        "exchange",
        "mode",
        "db_name"
    ],
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
                EXCHANGE_COINBASE,
                EXCHANGE_BITSTAMP,
            ],
        },
        "contract_type": {
            "type": ["null", "string"],
            "enum": [
                None,
                CONTRACT_TYPE_THIS_WEEK,
                CONTRACT_TYPE_NEXT_WEEK,
                CONTRACT_TYPE_QUARTER,
            ],
        },
        "mode": {
            "type": "string",
            "enum": [
                MODE_ONLINE,
                MODE_OFFLINE,
                MODE_BACKTEST,
                MODE_STRATEGY,
            ],
        },
        "db_name": {
            "type": "string",
            "minLength": 1,
        },
        "backtest_id": {
            "type": ["string", "null"],
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
                SUBJECT_INVEST,
                SUBJECT_DIVEST,
                SUBJECT_FREEZE,
                SUBJECT_UNFREEZE,
                SUBJECT_SETTLE,
                SUBJECT_TRANSFER_IN,
                SUBJECT_TRANSFER_OUT,
            ],
        },
        "amount": {
            "type": "number",
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
        self._trade_type = kwargs.get("trade_type")
        self._mode = kwargs.get("mode")
        self._backtest_id = kwargs.get("backtest_id")
        self._settle_mode = kwargs.get("settle_mode") or SETTLE_MODE_BASIS
        self._settle_currency = self._symbol.split("_")[self._settle_mode - 1]

        self._db_name = kwargs.get("db_name_asset") or kwargs.get("db_name")
        self._asset_table_name = self.__ASSET_TABLE_NAME_FORMAT__.format(
            trade_type=self._trade_type,
            mode=self._mode if self._mode == MODE_BACKTEST else "strategy",
        )
        self._account_flow_table_name = self.__ACCOUNT_FLOW_TABLE_NAME_FORMAT__.format(
            trade_type=self._trade_type,
            mode=self._mode if self._mode == MODE_BACKTEST else "strategy",
        )

    def __insert_account_flow_item(self, **kwargs):
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
        conn = Conn(self._db_name)
        conn.insert(
            """INSERT INTO {} (symbol, exchange, settle_mode, settle_currency, backtest_id, 
            subject, amount, position, timestamp, datetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """.format(self._account_flow_table_name),
            (
                self._symbol, self._exchange, self._settle_mode, self._settle_currency, self._backtest_id,
                kwargs.get("subject"), kwargs.get("amount"), kwargs.get("position"),
                kwargs.get("timestamp"), kwargs.get("datetime"),
            ),
        )

    def __invest(self, amount: int, position: float, timestamp: int, datetime: str):
        if amount <= 0 or position < 0.0:
            raise RuntimeError("invest func param error. amount <= 0 and position < 0.0. ")
        return self.__insert_account_flow_item(
            subject=SUBJECT_INVEST,
            amount=amount,
            position=position,
            timestamp=timestamp,
            datetime=datetime,
        )

    def __settle(self, amount: int, position: float, timestamp: int, datetime: str):
        if position != 0.0:
            raise RuntimeError("settle func param error. position == 0.0")
        return self.__insert_account_flow_item(
            subject=SUBJECT_SETTLE,
            amount=amount,
            position=position,
            timestamp=timestamp,
            datetime=datetime,
        )

    def __transfer_in(self, amount: int, position: float, timestamp: int, datetime: str):
        if amount <= 0 or position < 0.0:
            raise RuntimeError("transfer_in func param error. amount > 0 and position >= 0. ")
        return self.__insert_account_flow_item(
            subject=SUBJECT_TRANSFER_IN,
            amount=amount,
            position=position,
            timestamp=timestamp,
            datetime=datetime,
        )

    def __transfer_out(self, amount: int, position: float, timestamp: int, datetime: str):
        if amount >= 0 or position > 0.0:
            raise RuntimeError("transfer_out func param error. amount < 0 and position <= 0.0. ")
        return self.__insert_account_flow_item(
            subject=SUBJECT_TRANSFER_OUT,
            amount=amount,
            position=position,
            timestamp=timestamp,
            datetime=datetime,
        )

    def __freeze(self, amount: int, position: float, timestamp: int, datetime: str):
        if amount >= 0 or position > 0.0:
            raise RuntimeError("freeze func param error. amount < 0 and position < 0.0. ")
        return self.__insert_account_flow_item(
            subject=SUBJECT_FREEZE,
            amount=amount,
            position=position,
            timestamp=timestamp,
            datetime=datetime,
        )

    def __unfreeze(self, amount: int, position: float, timestamp: int, datetime: str):
        if amount <= 0 or position < 0.0:
            raise RuntimeError("unfreeze func param error. amount > 0 and position > 0.0. ")
        return self.__insert_account_flow_item(
            subject=SUBJECT_UNFREEZE,
            amount=amount,
            position=position,
            timestamp=timestamp,
            datetime=datetime,
        )

    def __insert_asset_item(self, timestamp, datetime):
        position_total, asset_total = self.__calculate_total(timestamp)
        position_freeze, asset_freeze = self.__calculate_freeze(timestamp)
        position_sub, asset_sub = self.__calculate_sub(timestamp)

        conn = Conn(self._db_name)
        one = conn.query_one(
            """SELECT * FROM {} WHERE exchange = ? AND settle_mode = ? AND settle_currency = ? 
            AND timestamp = ? AND backtest_id = ?""".format(self._asset_table_name),
            (self._exchange, self._settle_mode, self._settle_currency, timestamp, self._backtest_id)
        )
        if one:
            conn.execute(
                """
                UPDATE {} SET asset_total = ?, asset_sub = ?, asset_freeze = ?, 
                position_total = ?, position_sub = ?, position_freeze = ? WHERE id = ? 
                """.format(self._asset_table_name),
                (
                    asset_total,
                    asset_sub,
                    asset_freeze,
                    position_total,
                    position_sub,
                    position_freeze,
                    one["id"],
                ),
            )
        else:
            conn.insert(
                """
                INSERT INTO {} (exchange, settle_mode, settle_currency, backtest_id, 
                asset_total, asset_sub, asset_freeze, 
                position_total, position_sub, position_freeze,
                timestamp, datetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """.format(self._asset_table_name),
                (
                    self._exchange,
                    self._settle_mode,
                    self._settle_currency,
                    self._backtest_id,
                    asset_total,
                    asset_sub,
                    asset_freeze,
                    position_total,
                    position_sub,
                    position_freeze,
                    timestamp,
                    datetime,
                ),
            )

        one = conn.query_one(
            """SELECT * FROM {} WHERE exchange = ? AND settle_mode = ? AND settle_currency = ? 
            AND timestamp > ? AND backtest_id = ? ORDER BY timestamp LIMIT 1""".format(self._asset_table_name),
            (self._exchange, self._settle_mode, self._settle_currency, timestamp, self._backtest_id)
        )
        if one:
            self.__insert_asset_item(one["timestamp"], one["datetime"])

    # calculate the total position and total asset
    def __calculate_total(self, timestamp: int) -> (float, float):
        query_sql = """
        SELECT SUM(position) AS position, SUM(amount)/100000000 AS amount FROM {} WHERE exchange = ?
         AND settle_mode = ? AND settle_currency = ? AND backtest_id = ? AND timestamp <= ?
         AND subject IN (?, ?, ?)""".format(self._account_flow_table_name)
        query_param = (
            self._exchange, self._settle_mode, self._settle_currency, self._backtest_id,
            timestamp, SUBJECT_INVEST, SUBJECT_DIVEST, SUBJECT_SETTLE,
        )
        conn = Conn(self._db_name)
        result = conn.query_one(query_sql, query_param)
        position_total = result.get("position") or 20
        asset_total = result.get("amount") or 0.0
        return position_total, asset_total

    # calculate the freeze position and freeze asset
    def __calculate_freeze(self, timestamp: int) -> (float, float):
        query_sql = """
            SELECT SUM(amount)/100000000 AS asset_freeze, SUM(position) AS position_freeze FROM {} 
            WHERE exchange = ? AND settle_mode = ? AND settle_currency = ? AND backtest_id = ? 
            AND timestamp <= ? AND subject IN (?, ?)
        """.format(self._account_flow_table_name)
        query_param = (
            self._exchange, self._settle_mode, self._settle_currency, self._backtest_id, timestamp,
            SUBJECT_FREEZE, SUBJECT_UNFREEZE,
        )
        conn = Conn(self._db_name)
        result = conn.query_one(query_sql, query_param)
        position_freeze = -(result.get("position_freeze") or 0.0)
        asset_freeze = -(result.get("asset_freeze") or 0.0)
        return position_freeze, asset_freeze

    # calculate the sub position and sub asset
    def __calculate_sub(self, timestamp: int) -> (float, float):
        query_sql = """
            SELECT SUM(amount)/100000000 AS asset_sub, SUM(position) AS position_sub FROM {} 
            WHERE exchange = ? AND settle_mode = ? AND settle_currency = ? AND backtest_id = ?
            AND timestamp <= ? AND subject IN (?, ?, ?)
        """.format(self._account_flow_table_name)
        query_param = (
            self._exchange, self._settle_mode, self._settle_currency, self._backtest_id,
            timestamp, SUBJECT_TRANSFER_IN, SUBJECT_TRANSFER_OUT, SUBJECT_SETTLE,
        )
        conn = Conn(self._db_name)
        result = conn.query_one(query_sql, query_param)
        position_sub, asset_sub = result["position_sub"], result["asset_sub"]
        return position_sub, asset_sub

    # 回测是初始化账户，主要是注资，设置总position
    def first_invest(
            self,
            asset_total: float,
            position_total: float,
            position_sub: float,
    ) -> None:
        m = moment.get(BIRTHDAY_BTC).to(self.get("timezone") or "Asia/Shanghai")
        query_sql = "SELECT * FROM {} WHERE exchange = ? AND settle_mode = ? AND settle_currency = ? AND subject = ?" \
                    " AND timestamp <= ? AND backtest_id = ? LIMIT 1".format(self._account_flow_table_name)
        query_param = (
            self._exchange,
            self._settle_mode,
            self._settle_currency,
            SUBJECT_INVEST,
            m.millisecond_timestamp,
            self._backtest_id,
        )

        conn = Conn(self._db_name)
        one = conn.query_one(query_sql, query_param)
        if one:
            return

        self.__invest(
            standard_number(asset_total),
            position_total,
            m.millisecond_timestamp,
            m.format("YYYY-MM-DD HH:mm:ss"),
        )
        self.__transfer_in(
            standard_number(asset_total * position_sub / position_total),
            position_sub,
            m.millisecond_timestamp,
            m.format("YYYY-MM-DD HH:mm:ss"),
        )
        self.__insert_asset_item(
            m.millisecond_timestamp,
            m.format("YYYY-MM-DD HH:mm:ss"),
        )

    def freeze(
            self,
            amount: float,
            position: float,
            timestamp: int,
    ) -> None:
        m = moment.get(timestamp).to("Asia/Shanghai")
        self.__freeze(
            -standard_number(amount),
            -position,
            m.millisecond_timestamp,
            m.format("YYYY-MM-DD HH:mm:ss"),
        )
        return self.__insert_asset_item(
            m.millisecond_timestamp,
            m.format("YYYY-MM-DD HH:mm:ss"),
        )

    def unfreeze_and_settle(
            self,
            unfreeze_asset: float,
            unfreeze_position: float,
            settle_asset: float,
            timestamp: int,
    ) -> None:
        m = moment.get(timestamp).to("Asia/Shanghai")
        self.__unfreeze(
            standard_number(unfreeze_asset),
            unfreeze_position,
            m.millisecond_timestamp,
            m.format("YYYY-MM-DD HH:mm:ss"),
        )
        self.__settle(
            standard_number(settle_asset),
            0.0,
            m.millisecond_timestamp,
            m.format("YYYY-MM-DD HH:mm:ss"),
        )
        return self.__insert_asset_item(
            m.millisecond_timestamp,
            m.format("YYYY-MM-DD HH:mm:ss"),
        )

    def load(self, timestamp: int) -> dict:
        sql = """
        SELECT * FROM {} WHERE exchange = ? AND settle_mode = ? AND settle_currency = ? 
        AND timestamp <= ? ORDER BY timestamp DESC, id DESC LIMIT 1""".format(self._asset_table_name)
        params = (
            self._exchange, self._settle_mode, self._settle_currency, timestamp,
        )

        if self._mode == MODE_BACKTEST:
            sql = """
            SELECT * FROM {} WHERE exchange = ? AND settle_mode = ? AND settle_currency = ? 
            AND timestamp <= ? AND backtest_id = ? ORDER BY timestamp DESC, id DESC LIMIT 1
            """.format(self._asset_table_name)
            params = (
                self._exchange, self._settle_mode, self._settle_currency,
                timestamp, self._backtest_id
            )

        conn = Conn(self._db_name)
        result = conn.query_one(sql, params)
        if result is None:
            raise RuntimeError("you must init_amount before load the asset. ")

        self["asset_total"] = result["asset_total"]
        self["asset_sub"] = result["asset_sub"]
        self["asset_freeze"] = result["asset_freeze"]

        self["position_total"] = result["position_total"]
        self["position_sub"] = result["position_sub"]
        self["position_freeze"] = result["position_freeze"]
        return self
