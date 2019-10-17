

class Param(object):
    def __init__(self):
        super().__init__(instance)
        self._param = self._instance["param"] if "param" in instance else None

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
