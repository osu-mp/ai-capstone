import csv
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

# get the project root as the parent of the parent directory of this file
ROOT_DIR = str(Path(__file__).parent.parent.absolute())
sys.path.append(ROOT_DIR)

from scripts.check_predicted_kills import *

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to test_data/motion_data
TEST_DATA_ROOT = os.path.join(ROOT_DIR, 'tests', 'test_data', 'predictions')


def compare_csv_files(csv_file1, csv_file2):
    """
    Compare the contents of two CSV files and count the number of differences.

    Args:
    csv_file1 (str): Path to the first CSV file.
    csv_file2 (str): Path to the second CSV file.

    Returns:
    tuple: A tuple containing a boolean indicating whether the contents of the two CSV files are identical,
           and an integer indicating the number of differences.
    """
    num_differences = 0

    with open(csv_file1, 'r') as file1, open(csv_file2, 'r') as file2:
        reader1 = csv.reader(file1)
        reader2 = csv.reader(file2)

        # Compare each row of the CSV files
        for row_num, (row1, row2) in enumerate(zip(reader1, reader2), start=1):
            if row1 != row2:
                num_differences += 1

        # Check if both CSV files have the same number of rows
        if len(list(reader1)) != len(list(reader2)):
            num_differences += abs(len(list(reader1)) - len(list(reader2)))

    return num_differences == 0, num_differences


class TestFilterModelPredictions(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()

    def test_filter_model_predictions(self):
        """
        Unit tests for exp999 prediction CSV
        :return:
        """
        test_csv = os.path.join(TEST_DATA_ROOT, 'exp999_user2024.csv')
        exp_csv = os.path.join(TEST_DATA_ROOT,  'exp999_user2024_filtered_expected.csv')
        act_csv = os.path.join(self.temp_dir, 'exp999_user_2024_filtered_actual.csv')

        # Call the function with the sample CSV file
        filter_model_predictions(test_csv, act_csv)

        # verify the generated csv matches the expected csv
        files_same, num_differences = compare_csv_files(exp_csv, act_csv)
        self.assertTrue(files_same, f"Files do not match, {num_differences=}")

    def test_check_kill_status(self):
            # Dummy data fram
            df = pd.DataFrame({'behavior': [
                beh_dict['STALK'],  # 0
                beh_dict['STALK'],  # 1
                beh_dict['STALK'],  # 2
                beh_dict['STALK'],  # 3
                beh_dict['STALK'],  # 4
                beh_dict['STALK'],  # 5
                beh_dict['WALK'],  # 6
                beh_dict['WALK'],  # 7
                beh_dict['KILL'],  # 8
                beh_dict['KILL'],  # 9
                beh_dict['KILL'],  # 10
                beh_dict['KILL'],  # 11
                beh_dict['KILL'],  # 12
                beh_dict['WALK'],  # 13
                beh_dict['WALK'],  # 14
                beh_dict['WALK'],  # 15
                beh_dict['FEED'],  # 16
                beh_dict['FEED'],  # 17
                beh_dict['WALK'],  # 18
                beh_dict['FEED']  # 19
            ]})

            # Test valid kill scenario
            status, msg = check_kill_status(df, 8, min_stalk_time=2, min_stalk_delay=3, min_kill_time=2,
                                              min_feed_delta=4, max_feed_delta=6, min_feed_time=1)
            self.assertTrue(status)

            # Test invalid kill scenario - not enough STALK behavior before the kill start
            status, msg = check_kill_status(df, 8, min_stalk_time=8, min_stalk_delay=3, min_kill_time=2,
                                              min_feed_delta=4, max_feed_delta=6, min_feed_time=1)
            self.assertFalse(status)

            # Test invalid kill scenario - STALK behavior is too far from the kill start
            status, msg = check_kill_status(df, 8, min_stalk_time=5, min_stalk_delay=1, min_kill_time=2,
                                              min_feed_delta=4, max_feed_delta=6, min_feed_time=1)
            self.assertFalse(status)

            # Test invalid kill scenario - KILL is too short
            status, msg = check_kill_status(df, 8, min_stalk_time=2, min_stalk_delay=3, min_kill_time=6,
                                              min_feed_delta=4, max_feed_delta=6, min_feed_time=1)
            self.assertFalse(status)

            # Test valid: FEED behavior occurs within min_feed_delta of the end of KILL behavior
            status, msg = check_kill_status(df, 8, min_stalk_time=4, min_stalk_delay=2,
                                              min_kill_time=3, min_feed_delta=4, max_feed_delta=6,
                                              min_feed_time=1)
            self.assertTrue(status)

            # Test case: Not enough instances of FEED behavior within min_feed_time
            status, msg = check_kill_status(df, 8, min_stalk_time=4, min_stalk_delay=2,
                                               min_kill_time=3, min_feed_delta=4, max_feed_delta=6,
                                               min_feed_time=2)
            self.assertFalse(status)

    def tearDown(self):
        # Remove the temporary directory and its contents
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

if __name__ == '__main__':
    unittest.main()
