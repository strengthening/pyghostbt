import unittest

from pyghostbt.util import get_contract_timestamp
from pyanalysis.moment import moment


class TestUtil(unittest.TestCase):
    def test_contract_info(self):
        ts = moment.now().millisecond_timestamp
        start_timestamp, swap_timestamp, due_timestamp = get_contract_timestamp(ts, "quarter")
        print(start_timestamp, swap_timestamp, due_timestamp)
