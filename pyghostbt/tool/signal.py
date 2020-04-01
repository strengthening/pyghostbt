from jsonschema import validate
# from typing import List
from typing import Dict
from pyanalysis.mysql import Conn
from pyghostbt.const import *

signal_input = {
    "type": "object",
    "required": ["trade_type", "symbol", "exchange", "db_name"],
    "properties": {
        "trade_type": {
            "type": "string",
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT],
        },
        "symbol": {
            "type": "string",
            "minLength": 1,
        },
        "exchange": {
            "type": "string",
            "minLength": 1,
        },
        "contract_type": {
            "type": "string",
            "enum": [CONTRACT_TYPE_THIS_WEEK, CONTRACT_TYPE_NEXT_WEEK, CONTRACT_TYPE_QUARTER, CONTRACT_TYPE_NONE],
        },
        "db_name": {
            "type": "string",
            "minLength": 1,
        }
    }
}


class Signal(object):
    __cache = {}

    def __init__(self, **kwargs):
        validate(instance=kwargs, schema=signal_input)
        self._symbol = kwargs.get("symbol")
        self._exchange = kwargs.get("exchange")
        self._trade_type = kwargs.get("trade_type")
        self._contract_type = kwargs.get("contract_type") or CONTRACT_TYPE_NONE
        self._db_name = kwargs.get("db_name", "default")

        # self.__cache = {}

    def get_metadata(self, signal_name: str) -> dict:
        if signal_name in Signal.__cache:
            return Signal.__cache[signal_name]

        conn = Conn(self._db_name)
        metadata = conn.query_one(
            "SELECT * FROM signal_metadata"
            " WHERE symbol = ? AND exchange = ? AND trade_type = ? AND contract_type = ? AND signal_name = ? ",
            (self._symbol, self._exchange, self._trade_type, self._contract_type, signal_name),
        )
        if metadata is None:
            raise RuntimeError("Can not find the meta in database. ")
        Signal.__cache[signal_name] = metadata
        return metadata

    def in_signal(self, signal_name: str, timestamp: int) -> bool:
        meta = self.get_metadata(signal_name)
        signal_id = meta["signal_id"]

        conn = Conn(self._db_name)
        dataset = conn.query_one(
            "SELECT * FROM signal_dataset WHERE signal_id = ? AND start_timestamp >= ? AND finish_timestamp < ?"
            " ORDER BY start_timestamp DESC LIMIT 1",
            (signal_id, timestamp, timestamp),
        )
        return not (dataset is None)

    def get_value(self, signal_name: str, timestamp: int) -> Dict:
        signal_id = self.get_metadata(signal_name)["signal_id"]
        return self._value_by_id(signal_id, timestamp)

    def _value_by_id(self, signal_id: int, timestamp: int):
        conn = Conn(self._db_name)
        dataset = conn.query_one(
            "SELECT * FROM signal_dataset WHERE signal_id = ? AND start_timestamp >= ? AND finish_timestamp < ?"
            " ORDER BY start_timestamp DESC LIMIT 1",
            (signal_id, timestamp, timestamp),
        )
        return dataset
