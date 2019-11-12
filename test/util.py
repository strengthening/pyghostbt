import unittest

from pyghostbt.util import get_contract_info
from pyanalysis.moment import moment


class TestUtil(unittest.TestCase):
    def test_contract_info(self):
        ts = moment.now().millisecond_timestamp
        _, swap, _ = get_contract_info(ts, "next_week")
        print(swap, _)
