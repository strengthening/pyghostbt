from jsonschema import validate
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

    def get_value(self, fact_name: str, timestamp: int):
        conn = Conn(self._db_name)
        meta = conn.query_one(
            "SELECT * FROM factor_metadata WHERE symbol = ? AND trade_type = ? AND factor_name = ?",
            (self._symbol, self._trade_type, fact_name),
        )

        if meta is None:
            raise RuntimeError(
                "Can not find the factor, trade_type: {}, symbol: {}, factor_name: {}".format(
                    self._trade_type,
                    self._symbol,
                    fact_name,
                )
            )

        fact_data = conn.query_one(
            "SELECT factor_value FROM factor_dataset"
            " WHERE factor_id = ? AND timestamp <= ? ORDER BY timestamp DESC LIMIT 1",
            (meta["id"], timestamp),
        )

        if fact_data is None:
            raise RuntimeError("Can not find the factor value, there have no value in database. ")
        return fact_data["factor_value"]
