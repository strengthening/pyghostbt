from jsonschema import validate
from pyanalysis.mysql import *
from pyghostbt.const import *

# 海龟天数
PARAM_NAME_TURTLE_DAYS = "turtle_days"
# 仓位 必须是float且小数点后面1位。
PARAM_NAME_POSITION = "position"
# 相对于1 position 账户的损失，负数
PARAM_NAME_MAX_REL_LOSS = "max_rel_loss"
# 多：最大止损价/下单价-1 空：1-最大止损价/下单价，负数
PARAM_NAME_MAX_ABS_LOSS = "max_abs_loss"
# 多：最大止盈利价/下单价-1 空：1-最大止盈价/下单价，正数
PARAM_NAME_MAX_ABS_PROFIT = "max_abs_profit"

param_input = {
    "type": "object",
    "required": [PARAM_NAME_POSITION, PARAM_NAME_MAX_ABS_LOSS],
    "properties": {
        PARAM_NAME_TURTLE_DAYS: {"type": "integer", "minimum": 0, "maximum": 30},
        PARAM_NAME_POSITION: {"type": "number", "multipleOf": 0.1, "minimum": 0.1, "maximum": 5},
        PARAM_NAME_MAX_REL_LOSS: {"type": "number", "maximum": -0.00000001},
        PARAM_NAME_MAX_ABS_LOSS: {"type": "number", "maximum": 1.0, "minimum": -1.0},
        PARAM_NAME_MAX_ABS_PROFIT: {"type": "number", "minimum": 0.00000001}
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
            "enum": [MODE_ONLINE, MODE_OFFLINE, MODE_BACKTEST],
        },
        "backtest_id": {
            "type": "string",
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
            mode=self._mode,
        )

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

        params = []
        for param_name in self:
            if isinstance(self[param_name], int):
                params.append(
                    (instance_id, param_name, PARAM_TYPE_INTEGER, str([param_name]))
                )
            elif isinstance(self[param_name], float):
                params.append(
                    (instance_id, param_name, PARAM_TYPE_FLOAT, str(self[param_name]))
                )
            else:
                params.append(
                    (instance_id, param_name, PARAM_TYPE_STRING, self[param_name])
                )
        if len(params) == 0:
            return

        conn = Conn(self._db_name)
        param_future_sql = "INSERT INTO {} (instance_id, param_name, param_type, param_value) VALUES ".format(
            self._table_name,
        )
        param_future_sql += "(%s, %s, %s, %s), " * len(params)
        param_future_sql = param_future_sql[:-2]
        sql_params = ()
        for param in params:
            sql_params += param
        conn.execute(param_future_sql, sql_params)
