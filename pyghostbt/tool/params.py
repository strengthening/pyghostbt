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
    "required": ["instance_id", "trade_type", "db_name", "mode"],
    "properties": {
        "instance_id": {
            "type": "integer"
        },
        "trade_type": {
            "type": "string",
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT]
        },
        "db_name": {
            "type": "string", "minLength": 1
        },
        "mode": {
            "type": "string",
            "enum": [MODE_STRATEGY, MODE_BACKTEST],
        },
        PARAM_NAME_TURTLE_DAYS: {"type": "integer", "minimum": 0, "maximum": 30},
        PARAM_NAME_POSITION: {"type": "number", "multipleOf": 0.1, "minimum": 0.1, "maximum": 5},
        PARAM_NAME_MAX_REL_LOSS: {"type": "number", "maximum": -0.00000001},
        PARAM_NAME_MAX_ABS_LOSS: {"type": "number", "maximum": -0.00000001},
        PARAM_NAME_MAX_ABS_PROFIT: {"type": "number", "minimum": 0.00000001}
    }
}

param_save_input = {
    "type": "object",
    "required": [PARAM_NAME_POSITION, PARAM_NAME_MAX_ABS_LOSS],
    "properties": {
        PARAM_NAME_TURTLE_DAYS: {"type": "integer", "minimum": 0, "maximum": 30},
        PARAM_NAME_POSITION: {"type": "number", "multipleOf": 0.1, "minimum": 0.1, "maximum": 5},
    }
}


# param 从配置文件中读取到然后， 验证类型，是否定义过
class Param(object):
    __TABLE_NAME_FORMAT__ = "{trade_type}_params_{mode}"

    def __init__(self, **kwargs):
        super().__init__()

        validate(instance=kwargs, schema=param_input)
        self.db_name = kwargs.get("db_name")
        self.mode = kwargs.get("mode")
        self.trade_type = kwargs.get("trade_type")
        self.instance_id = kwargs.get("instance_id")

        self.table_name = self.__TABLE_NAME_FORMAT__.format(**kwargs)
        self._param = kwargs.copy()

        del self._param["db_name"]
        del self._param["trade_type"]
        del self._param["instance_id"]
        del self._param["mode"]

    def load(self):
        self._param = {}
        conn = Conn(self.db_name)
        results = conn.query(
            "SELECT * FROM {} WHERE instance_id = ?".format(self.table_name),
            (self.instance_id,),
        )

        for result in results:
            if result["param_type"] == PARAM_TYPE_INTEGER:
                self._param[result["param_name"]] = int(result["param_value"])
            elif result["param_type"] == PARAM_TYPE_FLOAT:
                self._param[result["param_name"]] = float(result["param_value"])
            else:
                self._param[result["param_name"]] = result["param_value"]

        return self._param

    def save(self):
        if self.mode == MODE_STRATEGY:
            raise RuntimeError("You can not save data in strategy mode")
        validate(instance=self._param, schema=param_save_input)

        params = []
        for param_name in self._param:
            if isinstance(self._param[param_name], int):
                params.append(
                    (self.instance_id, param_name, PARAM_TYPE_INTEGER, str(self._param[param_name]))
                )
            elif isinstance(self._param[param_name], float):
                params.append(
                    (self.instance_id, param_name, PARAM_TYPE_FLOAT, str(self._param[param_name]))
                )
            else:
                params.append(
                    (self.instance_id, param_name, PARAM_TYPE_STRING, self._param[param_name])
                )

        if params:
            conn = Conn(self.db_name)
            param_future_sql = "INSERT INTO {} (instance_id, param_name, param_type, param_value) VALUES ".format(
                self.table_name,
            )

            param_future_sql += "(%s, %s, %s, %s), " * len(params)
            param_future_sql = param_future_sql[:-2]
            sql_params = ()
            for param in params:
                sql_params += param
            conn.execute(param_future_sql, sql_params)
