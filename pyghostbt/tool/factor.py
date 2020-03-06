from jsonschema import validate
from typing import List
from pyanalysis.mysql import Conn
from pyghostbt.const import *

factor_input = {
    "type": "object",
    "required": ["trade_type", "symbol", "db_name"],
    "properties": {
        "trade_type": {
            "type": "string",
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT],
        },
        "symbol": {
            "type": "string",
            "minLength": 1,
        },
        "contract_type": {
            "type": "string",
            "enum": [CONTRACT_TYPE_THIS_WEEK, CONTRACT_TYPE_NEXT_WEEK, CONTRACT_TYPE_QUARTER],
        },
        "db_name": {
            "type": "string",
            "minLength": 1,
        }
    }
}


class Factor(object):
    def __init__(self, **kwargs):
        super().__init__()
        validate(instance=kwargs, schema=factor_input)

        self._symbol = kwargs.get("symbol")
        self._trade_type = kwargs.get("trade_type")
        self._contract_type = kwargs.get("contract_type")

        self._db_name = kwargs.get("db_name", "default")

    def get_metadata(self, fact_name: str) -> dict:
        conn = Conn(self._db_name)
        metadata = conn.query_one(
            "SELECT * FROM factor_metadata WHERE symbol = ? AND trade_type = ? AND factor_name = ? ",
            (self._symbol, self._trade_type, fact_name),
        )
        if metadata is not None:
            return metadata

        metadata = conn.query_one(
            "SELECT * FROM factor_metadata WHERE symbol = ? AND trade_type = ? AND factor_name = ? ",
            (self._symbol, TRADE_TYPE_SPOT, fact_name),
        )
        if metadata is None:
            raise RuntimeError("Can not find the meta in database. ")
        return metadata

    def get_value(self, fact_name: str, timestamp: int) -> float:
        meta = self.get_metadata(fact_name)
        return self._value_by_id(meta["id"], timestamp)

    def get_values(self, fact_name: str, start_timestamp: int, finish_timestamp: int) -> List[float]:
        meta = self.get_metadata(fact_name)
        return self._values_by_id(meta["id"], start_timestamp, finish_timestamp)

    def get_by_id(self, fact_id: int, timestamp: int) -> float:
        return self._value_by_id(fact_id, timestamp)

    def _value_by_id(self, fact_id: int, timestamp: int) -> float:
        conn = Conn(self._db_name)
        fact_data = conn.query_one(
            "SELECT factor_value FROM factor_dataset"
            " WHERE factor_id = ? AND timestamp <= ? ORDER BY timestamp DESC LIMIT 1",
            (fact_id, timestamp),
        )

        if fact_data is None:
            raise RuntimeError("Can not find the factor value, there have no value in database. ")
        return fact_data["factor_value"]

    def _values_by_id(self, fact_id: int, start_timestamp: int, finish_timestamp: int) -> List[float]:
        conn = Conn(self._db_name)
        fact_values = conn.query(
            "SELECT factor_value FROM factor_dataset"
            " WHERE factor_id = ? AND timestamp >= ? AND timestamp <= ? ORDER BY timestamp",
            (fact_id, start_timestamp, finish_timestamp),
        )

        return [f["factor_value"] for f in fact_values]
