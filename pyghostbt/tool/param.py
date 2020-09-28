from jsonschema import validate
from pyanalysis.mysql import *
from pyghostbt.const import *


# 海龟天数
PARAM_NAME_TURTLE_DAYS = "turtle_days"
# 仓位 必须是float且小数点后面1位。
PARAM_NAME_POSITION = "position"
# 仓位 稀释比例
PARAM_NAME_POSITION_DILUTION_RATIO = "position_dilution_ratio"
# 相对于1 position 账户的损失比例，负数
PARAM_NAME_MAX_REL_LOSS_RATIO = "max_rel_loss_ratio"
# 平仓价格对应于开仓价格的比率 l_price/o_price - 1，正负皆可
PARAM_NAME_MAX_ABS_LOSS_RATIO = "max_abs_loss_ratio"
# 下单价格间隔的值。
PARAM_NAME_PLACE_DIFF = "place_diff"
# 理想情况下的开仓价格
PARAM_NAME_NORMAL_OPEN_PRICE = "normal_open_price"
# 理想情况下的平仓价格
PARAM_NAME_NORMAL_LOSS_PRICE = "normal_loss_price"

PARAM_NAME_1ST_ABS_PROFIT_RATIO = "1st_abs_profit_ratio"

PARAM_NAME_2ND_ABS_PROFIT_RATIO = "2nd_abs_profit_ratio"


param_input = {
    "type": "object",
    # "required": [PARAM_NAME_POSITION, PARAM_NAME_MAX_ABS_LOSS],
    "properties": {
        PARAM_NAME_TURTLE_DAYS: {"type": "integer", "minimum": 0, "maximum": 30},
        PARAM_NAME_POSITION: {"type": "number", "minimum": 0.1, "maximum": 5},
        PARAM_NAME_POSITION_DILUTION_RATIO: {"type": "number", "minimum": 0, "maximum": 1},
        PARAM_NAME_MAX_REL_LOSS_RATIO: {"type": "number", "maximum": -0.00000001},
        PARAM_NAME_MAX_ABS_LOSS_RATIO: {"type": "number", "maximum": 1.0, "minimum": -1.0},
        PARAM_NAME_1ST_ABS_PROFIT_RATIO: {"type": "number", "maximum": 20.0, "minimum": -1.0},
        PARAM_NAME_2ND_ABS_PROFIT_RATIO: {"type": "number", "maximum": 20.0, "minimum": -1.0},
        PARAM_NAME_PLACE_DIFF: {"type": "integer"},
    },
}

param_config = {
    "type": "object",
    "required": ["trade_type", "db_name", "mode"],
    "properties": {
        "trade_type": {
            "type": "string",
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT]
        },
        "db_name": {
            "type": "string", "minLength": 1
        },
        "mode": {
            "type": "string",
            "enum": [MODE_ONLINE, MODE_OFFLINE, MODE_BACKTEST, MODE_STRATEGY],
        },
        "backtest_id": {
            "type": ["string", "null"],
            "minLength": 32,
            "maxLength": 32
        },
    }
}


# param 从配置文件中读取到然后， 验证类型，是否定义过
class Param(dict):
    __TABLE_NAME_FORMAT__ = "{trade_type}_param_{mode}"

    def __init__(self, param, **kwargs):
        # 先验证参数，再继承对应的方法
        validate(instance=param, schema=param_input)
        validate(instance=kwargs, schema=param_config)
        super().__init__(param)

        self._db_name = kwargs.get("db_name")
        self._mode = kwargs.get("mode")
        self._trade_type = kwargs.get("trade_type")
        self._table_name = self.__TABLE_NAME_FORMAT__.format(
            trade_type=self._trade_type,
            mode=MODE_BACKTEST if self._mode == MODE_BACKTEST else MODE_STRATEGY,
        )

    def add_item(self, param):
        validate(instance=param, schema=param_input)
        for param_name in param:
            self[param_name] = param[param_name]

    def load(self, instance_id):
        conn = Conn(self._db_name)
        results = conn.query(
            "SELECT * FROM {} WHERE instance_id = ?".format(self._table_name),
            (instance_id,),
        )
        for result in results:
            if result["param_type"] == PARAM_TYPE_INTEGER:
                self[result["param_name"]] = int(result["param_value"])
            elif result["param_type"] == PARAM_TYPE_FLOAT:
                self[result["param_name"]] = float(result["param_value"])
            else:
                self[result["param_name"]] = result["param_value"]

    def save(self, instance_id):
        if self._mode != MODE_BACKTEST:
            raise RuntimeError("You only can save data in backtest mode")
        # 入库前保证属性没有被篡改
        validate(instance=self, schema=param_input)

        conn = Conn(self._db_name)
        for param_name in self:
            if isinstance(self[param_name], int):
                sql_param = (PARAM_TYPE_INTEGER, str(self[param_name]), instance_id, param_name)
            elif isinstance(self[param_name], float):
                sql_param = (PARAM_TYPE_FLOAT, str(self[param_name]), instance_id, param_name)
            else:
                sql_param = (PARAM_TYPE_STRING, self[param_name], instance_id, param_name)
            one = conn.query_one(
                "SELECT * FROM {} WHERE instance_id = ? AND param_name = ?".format(self._table_name),
                (instance_id, param_name)
            )

            if one:
                conn.execute(
                    "UPDATE {} SET param_type = ?, param_value = ?"
                    " WHERE instance_id = ? AND param_name = ?".format(self._table_name),
                    sql_param,
                )
            else:
                conn.insert(
                    "INSERT INTO {} (param_type, param_value, instance_id, param_name)"
                    " VALUES (?, ?, ?, ?)".format(self._table_name),
                    sql_param
                )
