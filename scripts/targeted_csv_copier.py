import argparse
from collections import defaultdict
from datetime import datetime, timedelta
import glob
import logging
import os
import pandas as pd
import shutil
import unittest

"""
Script: targeted_csv_copier.py

Description:
This script extracts and saves a targeted subset of motion CSV data to reduce disk space usage. It processes an 
input CSV containing time-based clusters for wildlife data, identifies relevant daily motion data files from an 
input directory, and copies them to a specified output directory while maintaining the directory structure. 
Once the targeted data is saved, the original input directory can be safely deleted to conserve disk space.

The script supports adjusting cluster times, including additional days' data based on a configurable buffer period, 
and dry run mode to validate the process without actual file copying. It also includes unit tests to ensure 
functionality and robustness.

Features:
- Reads an input CSV file with required columns: `cougID`, `species`, `cluster_start_MST`.
- Adjusts cluster start times by a configurable hour offset (`--hour_offset`), defaulting to 7 (Mountain Time to UTC).
- Copies daily motion data files based on adjusted times and a buffer window (`--buffer_hours`), defaulting to 6 hours.
- Maintains the directory structure during file copying.
- Includes a dry run mode (`--dry_run`) to simulate operations without making changes.
- Logs missing files and generates a detailed summary of copied and missing files.
- Provides a built-in unit testing mode (`--run_tests`) for verifying script functionality.

Arguments:
- `--input_dir`: Directory containing extracted daily motion data files (binv2 format).
- `--output_dir`: Directory to store the processed subset of CSV files.
- `--input_csv`: Path to the input CSV file containing cluster times.
- `--hour_offset`: Number of hours to adjust cluster start times (default: 7 for Mountain Time to UTC).
- `--buffer_hours`: Buffer period in hours to include adjacent days' data (default: 6 hours).
- `--dry_run`: Simulates the process without copying files.
- `--run_tests`: Runs unit tests to validate script behavior.

Usage:
python targeted_csv_copier.py --input_dir <input_directory> --output_dir <output_directory> --input_csv <input_csv_file>
"""


logging.basicConfig(level=logging.INFO, format='%(message)s')


def adjust_time(cluster_start, hour_offset):
    """Adjust the time by the given hour offset."""
    try:
        if cluster_start is None or pd.isnull(cluster_start):
            raise ValueError("cluster_start cannot be None or NaN")
        if isinstance(cluster_start, str) and len(cluster_start.split(" ")) == 1:
            cluster_start += " 00:00:00"

        time = datetime.strptime(cluster_start, "%Y-%m-%d %H:%M:%S")
        return time + timedelta(hours=hour_offset)
    except Exception as e:
        raise ValueError(f"Error parsing time for cluster_start '{cluster_start}': {e}")


def copy_csv_files(input_dir, output_dir, coug_id, additional_dates, copied_files, missing_files):
    """Copy the target CSV and additional date files to the output directory."""
    for date in additional_dates:
        csv_path = os.path.join(
            input_dir,
            f"{coug_id}_*",
            "MotionData_*",
            date.strftime("%Y"),
            date.strftime("%m %b"),
            date.strftime("%d"),
            f"{date.strftime('%Y-%m-%d')}.csv",
        )

        # Resolve glob pattern to an actual file path
        matching_files = list(glob.glob(csv_path))
        if not matching_files:
            missing_files[coug_id].append(csv_path)
            continue

        target_file = matching_files[0]
        relative_path = os.path.relpath(target_file, input_dir)
        destination_file = os.path.join(output_dir, relative_path)

        # Create intermediate directories if necessary
        if args.dry_run:
            logging.info(f"Dry run: Would copy {target_file} to {destination_file}")
        else:
            os.makedirs(os.path.dirname(destination_file), exist_ok=True)
            shutil.copyfile(target_file, destination_file)
        copied_files[coug_id].append(target_file)


def process(input_dir, output_dir, input_csv, hour_offset, buffer_hours):
    """Main processing logic."""
    # Load the input CSV
    df = pd.read_csv(input_csv)

    # Dictionaries to track copied and missing files (key is cougar name, value is list of files)
    copied_files = defaultdict(list)
    missing_files = defaultdict(list)

    for _, row in df.iterrows():
        coug_id = row["cougID"]
        species = row["species"]
        cluster_start = row["cluster_start_MST"]

        # Adjust the time and determine additional dates to copy
        adjusted_time = adjust_time(cluster_start, hour_offset)
        additional_dates = [adjusted_time]
        if adjusted_time.hour <= buffer_hours:
            additional_dates.append(adjusted_time - timedelta(days=1))
            logging.info(f"Adjusted time close to PREV day, adding additional date ({coug_id=}, {cluster_start=})")
        if adjusted_time.hour >= (24 - buffer_hours):
            additional_dates.append(adjusted_time + timedelta(days=1))
            logging.info(f"Adjusted time close to NEXT day, adding additional date ({coug_id=}, {cluster_start=})")

        # Copy the required CSV files
        copy_csv_files(input_dir, output_dir, coug_id, additional_dates, copied_files, missing_files)

    # Print details of missing files
    if missing_files:
        logging.info("\nDetails of Missing Files:")
        for coug_id in sorted(missing_files.keys()):
            logging.info(f"Coug ID: {coug_id}")
            for file in missing_files[coug_id]:
                logging.info(f"\t{file}")
    else:
        logging.info("All files found/copied!")
    # Print a summary for each cougID
    logging.info("\nSummary of Processing:")
    for coug_id in sorted(set(copied_files.keys()).union(missing_files.keys())):
        logging.info(f"Coug ID: {coug_id}\tCopied: {len(copied_files[coug_id]):3d} Missing: {len(missing_files[coug_id]):3d}")

    total_copied = sum(len(v) for v in copied_files.values())
    total_missing = sum(len(v) for v in missing_files.values())
    total_files = total_copied + total_missing

    logging.info(f"Total files processed: {total_files}")
    logging.info(f"Files successfully copied: {total_copied}")
    logging.info(f"Files missing: {total_missing}")
    if args.dry_run:
        logging.warning("\nThis was a dry run, no files were actually copied!")


def validate_input_csv(input_csv):
    """Validate the input CSV for required columns."""
    required_columns = {"cougID", "species", "cluster_start_MST"}
    df = pd.read_csv(input_csv)
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"Input CSV is missing required columns: {', '.join(missing_columns)}")


def validate_params(input_dir, output_dir, input_csv, buffer_hours):
    """Validate input parameters."""
    if not os.path.isdir(input_dir):
        raise ValueError(f"Input directory does not exist: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)
    if not os.path.isdir(output_dir):
        raise ValueError(f"Output directory cannot be created: {output_dir}")

    if not os.path.isfile(input_csv):
        raise ValueError(f"Input CSV does not exist: {input_csv}")
    validate_input_csv(input_csv)

    if buffer_hours < 0 or buffer_hours > 24:
        raise ValueError(f"Buffer hours must be between 0 and 24: {buffer_hours=}")

class TestScriptFunctions(unittest.TestCase):
    def test_adjust_time(self):
        # Test with a valid date string
        cluster_start = "2024-11-27 12:00:00"
        self.assertEqual(
            adjust_time(cluster_start, 5), datetime(2024, 11, 27, 17, 0, 0)
        )
        # Test with no time provided
        cluster_start = "2024-11-27"
        self.assertEqual(
            adjust_time(cluster_start, -12), datetime(2024, 11, 26, 12, 0, 0)
        )
        # Test with a null cluster_start
        self.assertRaises(ValueError, adjust_time, None, 5)

    def test_validate_input_csv(self):
        # Create a temporary CSV file
        temp_csv = "temp_input.csv"
        valid_data = "cougID,species,cluster_start_MST\nF202,ELK,2024-11-27 12:00:00\n"
        with open(temp_csv, "w") as f:
            f.write(valid_data)

        # Validate with no missing columns
        validate_input_csv(temp_csv)

        # Validate with missing columns
        invalid_data = "cougID,cluster_start_MST\nF202,2024-11-27 12:00:00\n"
        with open(temp_csv, "w") as f:
            f.write(invalid_data)

        self.assertRaises(ValueError, validate_input_csv, temp_csv)

        # Clean up
        os.remove(temp_csv)

    def test_validate_params(self):
        # Test with valid directories and CSV
        temp_dir = "temp_dir"
        temp_csv = "temp_input.csv"
        os.makedirs(temp_dir, exist_ok=True)
        with open(temp_csv, "w") as f:
            f.write("cougID,species,cluster_start_MST\nF202,ELK,2024-11-27 12:00:00\n")

        validate_params(temp_dir, temp_dir, temp_csv, 6)

        # Test with invalid input directory
        self.assertRaises(ValueError, validate_params, "nonexistent_dir", temp_dir, temp_csv, 6)

        # Test with invalid buffer_hours
        self.assertRaises(ValueError, validate_params, temp_dir, temp_dir, temp_csv, 30)

        # Clean up
        os.remove(temp_csv)
        os.rmdir(temp_dir)


def run_tests():
    unittest.main(argv=["first-arg-is-ignored"], exit=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy targeted CSV files based on input parameters.")
    parser.add_argument("--input_dir", required=True, help="Directory containing all binv2 files.")
    parser.add_argument("--output_dir", required=True, help="Directory where targeted CSV files will be copied.")
    parser.add_argument("--hour_offset", type=int, default=7, help="Number of hours to adjust input CSV times.")
    parser.add_argument("--buffer_hours", type=int, default=6,
                        help=(
                            "Specifies a buffer period (in hours) around the cluster start time. "
                            "If the adjusted time is within this many hours of the start of the previous day (12:00 AM), "
                            "the previous day's CSV will also be copied. "
                            "Similarly, if the adjusted time is within this many hours of the end of the current day (11:59 PM), "
                            "the next day's CSV will also be copied."
                        ))
    parser.add_argument("--input_csv", required=True, help="CSV file containing target times.")
    parser.add_argument("--dry_run", action="store_true", help="Run without copying files (for testing).")
    parser.add_argument("--run_tests", action="store_true", help="Run unit tests.")

    args = parser.parse_args()

    if args.run_tests:
        run_tests()
    else:
        try:
            validate_params(args.input_dir, args.output_dir, args.input_csv, args.buffer_hours)
            process(args.input_dir, args.output_dir, args.input_csv, args.hour_offset, args.buffer_hours)
        except ValueError as e:
            logging.info(f"Error: {e}")
            exit(1)



