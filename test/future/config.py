import unittest

from pyghostbt.future.models import *


class TestConfig(unittest.TestCase):
    def test_debug_handler_logger(self):
        conf = Config({})
        print(conf)
        # debug_handler = DebugHandler()
        # logger = logging.getLogger("debug")
        # logger.addHandler(debug_handler)
        # logger.setLevel(debug_handler.level)
        #
        # logger.debug("some log about debug! ")
        # logger.info("some log about info! ")
        #
        # try:
        #     1 / 0
        # except Exception as e:
        #     logger.exception(e)
