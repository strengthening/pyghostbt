
class Instance(object):
    def __init__(self, instance):
        self._instance = instance
        self._instance_json_format = json.dumps(instance)  # 为了生成多个 instance做准备
        self._symbol = instance["order"]["symbol"]
        self._exchange = instance["order"]["exchange"]
        self._strategy = instance["order"]["strategy"]
        self._intervals = {
            "weekly": 7 * 24 * 60 * 60 * 1000,
            "daily": 24 * 60 * 60 * 1000,
            "hourly": 60 * 60 * 1000,
            "minutely": 60 * 1000
        }

        if "mode" in instance:
            self._mode = instance["mode"]  # the mode is analysis or strategy
        else:
            self._mode = instance["mode"] or os.environ.get("MODE")

        if instance["order"]["status"] == "wait":
            self._contract_type = instance["order"]["open_contract_type"]
        else:
            # todo this maybe have bug！
            if "liquidate_contract_type" in instance["order"]:
                self._contract_type = instance["order"]["liquidate_contract_type"]
            else:
                self._contract_type = instance["order"]["open_contract_type"]

    def _check_instance(self):
        if self._instance:
            return True
        return False

    def _get_db_name(self):
        if self._mode == "analysis":
            return "ghost-spider"
        return "ghost"

    def _get_table_name(self, interval=''):
        if interval == "weekly":
            # if self._mode == "analysis":
            #     return "ticker_week_future_{}".format(self._symbol)
            return "kline_week_future_{}".format(self._symbol)
        else:
            if self._mode == "analysis":
                return "ticker_minute_future_{}".format(self._symbol)
            return "kline_min_future_{}".format(self._symbol)