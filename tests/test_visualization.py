import filecmp
import matplotlib.pyplot as plt
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

import numpy as np

# get the project root as the parent of the parent directory of this file
ROOT_DIR = str(Path(__file__).parent.parent.absolute())
sys.path.append(ROOT_DIR)

from scripts.check_predicted_kills import filter_model_predictions
from utils.visualization import *

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to test_data/motion_data
TEST_DATA_ROOT = os.path.join(ROOT_DIR, 'tests', 'test_data', 'predictions')


class TestPlotKillPredictions(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.test_dir)

    def test_plot_kill_predictions(self):
        # Compare generated plot with reference plot
        test_csv = os.path.join(TEST_DATA_ROOT, 'exp999_user2024.csv')
        df = pd.read_csv(test_csv, header=None, names=['behavior'])
        generated_fname = os.path.join(self.test_dir, 'test_plot_kill_predictions.png')
        reference_plot = os.path.join(TEST_DATA_ROOT, 'reference_plot.png')
        dummy_csv = os.path.join(self.test_dir, 'exp999_user2024.csv')
        dummy_csv, kill_statuses = filter_model_predictions(test_csv, dummy_csv, generated_fname)
        # plot_kill_predictions(df, kill_statuses, generated_fname)
        self.assertTrue(filecmp.cmp(generated_fname, reference_plot))

if __name__ == '__main__':
    unittest.main()
