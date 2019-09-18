import json
import os
import time
import datetime

from pyanalysis.database.mysql import *


class Config(object):
    def __init__(self, config):
        self._config = config
        Config.__check(config)

    @staticmethod
    def __check(self, config):

        must_exist_keys = [

            "mode",
            "symbol",
            "exchange",
            "contract_type",
            "strategy",
            "unit_amount",
            "lever",
            "interval",

            "open_type",
            "open_place_type",
            "open_times",
            "open_swap",

            "liquidate_type",
            "liquidate_place_type",
            "liquidate_times",
            "liquidate_swap",

            "param_position",
            "param_abs_loss_ratio",
        ]

        for key in must_exist_keys:
            if key not in config:
                raise RuntimeError("Can not find the %s in the config" % key)

        if config["mode"] != "strategy" and config["mode"] != "backtest":
            raise ConfigValueError("mode", config["mode"])

    def get_param(self):
        param = {
            "position": self._config["param_position"],
            "abs_loss_ratio": self._config["param_abs_loss_ratio"],
        }
        return param



class ConfigValueError(Exception):
    def __init__(self, key, value):
        self._key = key
        self._value = value

    def __str__(self):
        return "The config %s can not be %s" % (self._key, self._value)
