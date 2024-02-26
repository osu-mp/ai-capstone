import filecmp
import os
from pathlib import Path
from PIL import Image, ImageChops
import sys
import unittest
from datetime import datetime, timedelta

# from skimage import measure
# from skimage import io

# get the project root as the parent of the parent directory of this file
ROOT_DIR = str(Path(__file__).parent.parent.absolute())
sys.path.append(ROOT_DIR)

from utils.spreadsheet_utils import main as generate_main
from utils.spreadsheet_utils import get_motion_data

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to test_data/motion_data
TEST_DATA_ROOT = os.path.join(ROOT_DIR, 'tests', 'test_data', 'motion_data')

def compare_directories(dir1, dir2):
    # Compare the directories recursively
    dir_comparison = filecmp.dircmp(dir1, dir2)

    # Check if there are any differences in files or directories
    if dir_comparison.diff_files or dir_comparison.left_only or dir_comparison.right_only:
        print("Directories have different contents.")
        # Print the list of differing files and directories
        print("Differences in files:", dir_comparison.diff_files)
        print("Files only in", dir1 + ":", dir_comparison.left_only)
        print("Files only in", dir2 + ":", dir_comparison.right_only)
        return False
    else:
        print("Directories have the same contents.")
        return True

def compare_images(file1, file2):
    # import numpy as np
    # import cv2

    # # Load images
    # image1 = cv2.imread(file1)
    # image2 = cv2.imread(file2)

    # # Calculate the absolute difference between the images
    # difference = cv2.absdiff(image1, image2)

    # # Convert the difference to grayscale
    # gray_difference = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    # # Threshold the grayscale image to find areas with differences
    # _, threshold = cv2.threshold(gray_difference, 30, 255, cv2.THRESH_BINARY)

    # # Display the thresholded image or save it
    # cv2.imshow('Difference', threshold)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # return

    try:
        img1 = Image.open(file1)
        img2 = Image.open(file2)
        diff = ImageChops.difference(img1, img2)
        return diff.getbbox() is None  # Returns True if images are identical

    except IOError as e:
        print(f"Error: {e}")
        return False

def compare_images_in_directories(gold_dir, test_dir):
    files1 = [f for f in os.listdir(gold_dir) if f.lower().endswith('.png')]
    # files2 = [f for f in os.listdir(dir2) if f.lower().endswith('.png')]

    all_match = True
    match_count = 0
    for file1 in files1:        
        image1_path = os.path.join(gold_dir, file1)
        image2_path = os.path.join(test_dir, file1)

        result = compare_images(image1_path, image2_path)
        if result:
            match_count += 1
        else:
            print(f"Image {file1} in dirs {dir1} and {dir2} are NOT identical.")
            all_match = False
        # Uncomment the following line if you want to see non-identical pairs
        # else:
        #     print(f"Images {file1} and {file2} are different.")

    # print("All images match")
    print(f"{gold_dir=} {match_count=}")
    return all_match


def remove_log_files(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".log"):
            file_path = os.path.join(directory, filename)
            os.remove(file_path)
            print(f"Deleted: {file_path}")

class TestGenerateR(unittest.TestCase):
    def test_rscripts(self):
        
        test_dir = '/home/matthew/AI_Capstone/ai-capstone/rcode/jobs'
        gold_dir = '/home/matthew/AI_Capstone/ai-capstone/rcode/jobs_gold'
        # remove log files in rundir
        remove_log_files(test_dir)
        #self.assertTrue(compare_directories(test_dir, gold_dir))

    # def test_pngs(self):
    #     test_root = '/home/matthew/AI_Capstone/ai-capstone/plots'
    #     gold_root = '/home/matthew/AI_Capstone/ai-capstone/plots_gold'
    #     for dir in os.listdir(gold_root):
    #         test_dir = os.path.join(test_root, dir)
    #         gold_dir = os.path.join(gold_root, dir)
    #         self.assertTrue(compare_images_in_directories(gold_dir, test_dir))


class TestGetMotionData(unittest.TestCase):
    def setUp(self):
        self.data_root = TEST_DATA_ROOT
        self.start_date = datetime(2020, 12, 24)
        self.start_time = datetime.strptime("08:00:00", "%H:%M:%S").time()
        self.end_time = datetime.strptime("12:00:00", "%H:%M:%S").time()
        self.out_fp = "test_output.csv"
        self.sample_rate = 16

    def get_expected_samples(self, start_time, end_time, sample_rate=None):
        start_datetime = datetime.combine(datetime.now().date(), start_time)
        end_datetime = datetime.combine(datetime.now().date(), end_time)

        # Calculate duration of time window in seconds
        # add 1 second to account for samples in last second getting counted
        time_window_duration_seconds = (end_datetime - start_datetime).total_seconds() + 1

        # Calculate expected number of samples in the time window
        window_entries = time_window_duration_seconds * self.sample_rate
        return window_entries

    def test_end_time_provided(self):
        df = get_motion_data(self.data_root, self.start_date, self.start_time, end_time=self.end_time,
                             out_fp=self.out_fp)

        # Assuming start_time and end_time are datetime.time objects
        expected_samples = self.get_expected_samples(self.start_time, self.end_time)

        self.assertEqual(len(df), expected_samples)

    def test_duration_provided(self):
        duration = 2 * 60               # two hours
        df = get_motion_data(self.data_root, self.start_date, self.start_time, duration=duration, out_fp=self.out_fp)

        # total number of samples is duration length (in seconds) + 1 to account for all samples in first and last seconds
        expected_samples = (duration * 60 + 1) * self.sample_rate
        self.assertEqual(len(df), expected_samples)

    def test_start_offset_provided(self):
        duration = 1 * 60           # one hour duration
        start_offset = 30           # add 30 minutes to start
        df = get_motion_data(self.data_root, self.start_date, self.start_time, duration=duration, start_offset=start_offset, out_fp=self.out_fp)

        # total number of samples is duration length (in seconds) + 1 to account for all samples in first and last seconds
        expected_samples = (duration * 60 + 1) * self.sample_rate
        expected_samples += (start_offset * 60) * self.sample_rate
        self.assertEqual(len(df), expected_samples)

    def test_start_offset_previous_day(self):
        df = get_motion_data(self.data_root, self.start_date, self.start_time, duration=240, start_offset=480,
                             out_fp=self.out_fp)
        self.assertFalse(df.empty)

    def test_invalid_input(self):
        with self.assertRaises(ValueError) as context:
            get_motion_data(self.data_root, self.start_date, self.start_time, out_fp=self.out_fp)

        self.assertEqual(str(context.exception), "Either end_time or duration must be provided")



if __name__ == '__main__':
    # generate_main()
    unittest.main()