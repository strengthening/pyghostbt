from pyghostbt.const import *

INSTANCE_VALIDATE = {
    "type": "object",
    "required": [
        "id", "symbol", "exchange", "strategy",
        "status", "interval", "unit_amount",
        "asset_total", "asset_freeze",
        "param_position", "param_max_abs_loss_ratio",
        "wait_start_timestamp", "wait_start_datetime",
        "wait_finish_timestamp", "wait_finish_datetime",
        "open_start_timestamp", "open_start_datetime",
        "open_finish_timestamp", "open_finish_datetime",
        "open_expired_timestamp", "open_expired_datetime",
        "liquidate_start_timestamp", "liquidate_start_datetime",
        "liquidate_finish_timestamp", "liquidate_finish_datetime",
    ],
    "properties": {
        "id": {
            "type": "integer",
        },
        "symbol": {
            "type": "string",
        },
        "exchange": {
            "type": "string",
        },
        "contract_type": {
            "type": ["null", "string"],
            "enum": [
                None,
                CONTRACT_TYPE_THIS_WEEK,
                CONTRACT_TYPE_NEXT_WEEK,
                CONTRACT_TYPE_QUARTER,
                CONTRACT_TYPE_NONE,
            ],
        },
        "strategy": {
            "type": "string",
        },
        "status": {
            "type": "integer",
            "enum": [
                INSTANCE_STATUS_WAITING,
                INSTANCE_STATUS_OPENING,
                INSTANCE_STATUS_LIQUIDATING,
                INSTANCE_STATUS_FINISHED,
                INSTANCE_STATUS_ERROR,
            ],
        },
        "interval": {
            "type": "string",
            "enum": [
                KLINE_INTERVAL_1MIN,
                KLINE_INTERVAL_15MIN,
                KLINE_INTERVAL_1HOUR,
                KLINE_INTERVAL_4HOUR,
                KLINE_INTERVAL_1DAY,
                KLINE_INTERVAL_1WEEK,
            ],
        },
        "unit_amount": {
            "type": "number",
            "minimum": 0,
        },
        "lever": {
            "type": "integer",
            "enum": [1, 10, 20],
        },
        "asset_total": {
            "type": "number",
            "minimum": 0,
        },
        "asset_freeze": {
            "type": "number"
        },
        "param_position": {
            "type": "number"
        },
        "param_max_abs_loss_ratio": {
            "type": "number",
            "minimum": -0.5,
            "maximum": 0.5,
        },
        "wait_start_timestamp": {
            "type": "integer",
            "minimum": 1000000000000,
            "maximum": 3000000000000,
        },
        "wait_start_datetime": {
            "type": "string"
        },
        "wait_finish_timestamp": {
            "type": "integer",
            "minimum": 1000000000000,
            "maximum": 3000000000000,
        },
        "wait_finish_datetime": {
            "type": "string"
        },
        "open_start_timestamp": {
            "type": "integer",
        },
        "open_start_datetime": {
            "type": ["string", "null"],
        },
        "open_finish_timestamp": {
            "type": "integer",
        },
        "open_finish_datetime": {
            "type": ["string", "null"],
        },
        "open_expired_timestamp": {
            "type": "integer",
        },
        "open_expired_datetime": {
            "type": ["string", "null"],
        },
        "liquidate_start_timestamp": {
            "type": "integer",
        },
        "liquidate_start_datetime": {
            "type": ["string", "null"],
        },
        "liquidate_finish_timestamp": {
            "type": "integer",
        },
        "liquidate_finish_datetime": {
            "type": ["string", "null"],
        }
    }
}
