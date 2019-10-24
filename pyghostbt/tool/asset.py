# 资产管理

from jsonschema import validate
from pyghostbt.const import *
from pyanalysis.mysql import Conn
from pyanalysis.moment import moment

asset_input = {
    "type": "object",
    "required": ["trade_type", "symbol", "exchange", "mode", "db_name", "backtest_id"],
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


class Asset(object):
    __ASSET_TABLE_NAME_FORMAT__ = "{trade_type}_assets_{mode}"
    __ACCOUNT_FLOW_TABLE_NAME_FORMAT__ = "{trade_type}_account_flow_{mode}"

    def __init__(self, **kwargs):
        super().__init__()
        validate(instance=kwargs, schema=asset_input)

        self.symbol = kwargs.get("symbol")
        self.exchange = kwargs.get("exchange")
        self.trade_type = kwargs.get("trade_type")
        self.mode = kwargs.get("mode")
        self.backtest_id = kwargs.get("backtest_id")

        self.db_name = kwargs.get("db_name", "default")
        self.asset_table_name = self.__ASSET_TABLE_NAME_FORMAT__.format(
            trade_type=self.trade_type,
            symbol=self.mode,
        )
        self.account_flow_table_name = self.__ACCOUNT_FLOW_TABLE_NAME_FORMAT__.format(
            trade_type=self.trade_type,
            symbol=self.mode,
        )

    def __get_last_asset(self, timestamp):
        conn = Conn(self.db_name)
        if self.mode == MODE_BACKTEST:
            return conn

        return conn.query_one(
            "SELECT * FROM {} WHERE symbol = ? AND exchange = ? AND snapshot_timestamp < ?"
            " ORDER BY snapshot_timestamp DESC LIMIT 1".format(self.asset_table_name),
            (self.symbol, self.exchange, timestamp)
        )

    def __set_the_asset(self, timestamp):
        if self.mode != MODE_BACKTEST:
            raise RuntimeError("Only the backtest mode can init account by this function. ")
        conn = Conn(self.db_name)
        conn.query_one(
            """SELECT * FROM {} symbol = ? AND exchange = ? AND timestamp >= ?"""
        )


    def init_account(self, amount):
        if self.mode != MODE_BACKTEST:
            raise RuntimeError("Only the backtest mode can init account by this function. ")
        m = moment.get(BIRTHDAY_BTC)
        conn = Conn(self.db_name)
        conn.insert(
            """
            INSERT INTO {} (symbol, exchange, backtest_id, relate_id, subject,
             amount, `position`, timestamp, datetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """.format(self.account_flow_table_name),
            (
                self.symbol, self.exchange, self.backtest_id, -1, SUBJECT_INJECTION,
                amount, 0, m.millisecond_timestamp, m.format("YYYY-MM-DD HH:mm:ss"),
            )
        )

    def get_the_anchor_asset(self, open_position, open_timestamp, future_limit_position):
        asset_info = self.__get_last_asset(open_timestamp)
        if asset_info is None:
            raise RuntimeError("May be you should init_account. ")
        # 超过限制同时开仓的限制，则返回负数
        if (asset_info["future_opened_position"] + open_position) >= future_limit_position:
            return -1
        # 建仓原则，当有开仓的情况下。认为现在的总账户按照此开仓损失来看待。
        return asset_info["total_account_asset"] + asset_info["future_max_loss"]

    def lock_the_asset(self, snapshot_timestamp, position, max_margin, loss_asset):
        if self.mode != MODE_BACKTEST:
            raise RuntimeError("Only the backtest mode can lock the asset by this function. ")

        snapshot = moment.get(snapshot_timestamp, tzinfo="Asia/Shanghai")
        asset_info = self.__get_last_asset(snapshot_timestamp)

        total_account_asset = asset_info["total_account_asset"]
        future_account_asset = asset_info["future_account_asset"]

        future_max_margin = asset_info["future_max_margin"] + max_margin
        future_max_loss = asset_info["future_max_loss"] + loss_asset

        total_account_position = asset_info["total_account_position"]
        future_account_position = asset_info["future_account_position"]
        future_opened_position = asset_info["future_opened_position"] + position

        conn = Conn(self.db_name)
        conn.insert(
            """
            INSERT INTO {} (symbol, exchange, total_account_asset, future_account_asset, future_max_margin, 
            future_max_loss, total_account_position, future_account_position, future_opened_position,
            snapshot_timestamp, snapshot_datetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """.format(self.asset_table_name),
            (
                self.symbol, self.exchange, total_account_asset, future_account_asset, future_max_margin,
                future_max_loss, total_account_position, future_account_position, future_opened_position,
                snapshot_timestamp, snapshot.format("YYYY-MM-DD HH:mm:ss"),
            ),
        )

    def unlock_the_asset(self, snapshot_timestamp, position, max_margin, loss_asset, pnl_asset):
        if self.mode != MODE_BACKTEST:
            raise RuntimeError("Only the backtest mode can unlock the asset by this function. ")

        snapshot = moment.get(snapshot_timestamp, tzinfo="Asia/Shanghai")
        asset_info = self.__get_last_asset(snapshot_timestamp)

        total_account_asset = asset_info["total_account_asset"] + pnl_asset
        future_account_asset = total_account_asset * asset_info["future_account_position"] / asset_info[
            "total_account_position"]

        future_max_margin = asset_info["future_max_margin"] - max_margin
        future_max_loss = asset_info["future_max_loss"] - loss_asset

        total_account_position = asset_info["total_account_position"]
        future_account_position = asset_info["future_account_position"]
        future_opened_position = asset_info["future_opened_position"] - position

        conn = Conn(self.db_name)
        conn.insert(
            """
            INSERT INTO {} (symbol, exchange, total_account_asset, future_account_asset, future_max_margin, 
            future_max_loss, total_account_position, future_account_position, future_opened_position,
            snapshot_timestamp, snapshot_datetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """.format(self.asset_table_name),
            (
                self.symbol, self.exchange, total_account_asset, future_account_asset, future_max_margin,
                future_max_loss, total_account_position, future_account_position, future_opened_position,
                snapshot_timestamp, snapshot.format("YYYY-MM-DD HH:mm:ss"),
            ),
        )
