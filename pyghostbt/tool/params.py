from pyanalysis.mysql import *
from pyghostbt.const import *

# 海龟天数
PARAM_NAME_TURTLE_DAYS = "turtle_days"
# 仓位
PARAM_NAME_POSITION = "position"
# 相对于1 position 账户的损失，负数
PARAM_NAME_MAX_REL_LOSS = "max_rel_loss"
# 多：最大止损价/下单价-1 空：1-最大止损价/下单价，负数
PARAM_NAME_MAX_ABS_LOSS = "max_abs_loss"
# 多：最大止盈利价/下单价-1 空：1-最大止盈价/下单价，正数
PARAM_NAME_MAX_ABS_PROFIT = "max_abs_profit"

param_input = {
    "type": "object",
    "required": ["instance_id", "trade_type"],
    "properties": {
        "instance_id": {"type": "integer"},
        "trade_type": {
            "type": "string",
            "enum": [TRADE_TYPE_FUTURE, TRADE_TYPE_SWAP, TRADE_TYPE_MARGIN, TRADE_TYPE_SPOT]
        },
        PARAM_NAME_TURTLE_DAYS: {"type": "integer", "minimum": 0, "maximum": 30},
        PARAM_NAME_POSITION: {"type": "number", "minimum": 0.1, "maximum": 5},
        PARAM_NAME_MAX_REL_LOSS: {"type": "number", "maximum": -0.00000001},
        PARAM_NAME_MAX_ABS_LOSS: {"type": "number", "maximum": -0.00000001},
        PARAM_NAME_MAX_ABS_PROFIT: {"type": "number", "minimum": 0.00000001}
    }
}

param_item = {
    "type": "object",
    "required": ["instance_id", "param_name", "param_type", "param_value"],
    "properties": {
        "instance_id": {"type": "integer"},
        "param_name": {"type": "string"},
        "param_type": {"type": "string"},
        "param_value": {"type": "string"},
    }
}


# param 从配置文件中读取到然后， 验证类型，是否定义过
class Param(object):
    def __init__(self, **kwargs):
        super().__init__()
        if "instance_id" not in kwargs:
            raise RuntimeError("The param must has the instance_id")
        # self._param = self._instance["param"] if "param" in instance else None

    def list(self):
        params = []
        for key in self._param:
            if isinstance(self._param[key], int):
                params.append([key, "int", str(self._param[key])])
            elif isinstance(self._param[key], str):
                params.append([key, "string", str(self._param[key])])
            elif isinstance(self._param[key], float):
                params.append([key, "float", str(self._param[key])])
            else:
                pass
        return params

    def get(self, order_id):
        conn = Conn(self._get_db_name())
        params = conn.query("""SELECT * FROM order_future_param WHERE order_id = %s""", (order_id,))

        _params = {}
        for param in params:
            if param["type"] == "int":
                _params[param["name"]] = int(param["value"])
            elif param["type"] == "float":
                _params[param["name"]] = float(param["value"])
            else:
                _params[param["name"]] = param["value"]

        return _params

    def sync(self, order_id):
        param_future_sql = """INSERT INTO order_future_param (`order_id`, `name`, `type`, `value`) VALUES """
        params = self.list()
        if params:
            conn = Conn(self._get_db_name())
            param_future_sql += "(%s, %s, %s, %s), " * len(params)
            param_future_sql = param_future_sql[:-2]
            sql_params = ()
            for param in params:
                sql_params += (order_id, param[0], param[1], param[2])
            conn.execute(param_future_sql, sql_params)
