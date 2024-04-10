import unittest
from datetime import datetime
import pytz
from pathlib import Path
import sys

# get the project root as the parent of the parent directory of this file
ROOT_DIR = str(Path(__file__).parent.parent.absolute())
sys.path.append(ROOT_DIR)

from utils.general import  *

class TestMstToUtcWithDst(unittest.TestCase):
    def test_standard_time(self):
        # Test with standard time (MST)
        mst_datetime_str = "2024-01-01 12:00:00"
        expected_utc = "2024-01-01 19:00:00"
        self.assertEqual(mst_to_utc_with_dst(mst_datetime_str), expected_utc)

    def test_daylight_saving_time(self):
        # Test with daylight saving time (MDT)
        mst_datetime_str = "2024-06-01 12:00:00"
        expected_utc = "2024-06-01 18:00:00"
        self.assertEqual(mst_to_utc_with_dst(mst_datetime_str), expected_utc)

    def test_ambiguous_time(self):
        # Test with ambiguous time (end of daylight saving time)
        mst_datetime_str = "2024-11-04 01:30:00"  # 1:30 AM MST (before DST ends)
        expected_utc = "2024-11-04 08:30:00"  # This time could be interpreted as both MST and MDT
        self.assertEqual(mst_to_utc_with_dst(mst_datetime_str), expected_utc)

if __name__ == '__main__':
    unittest.main()
