import csv
from datetime import datetime, timezone, timedelta
import os
import pandas as pd
from pathlib import Path
import sys

# get the project root as the parent of the parent directory of this file
ROOT_DIR = str(Path(__file__).parent.parent.parent.absolute())
sys.path.append(ROOT_DIR)

from utils.general import mst_to_utc_with_dst

animal_id = 210
sex = 'F'
init_kill_id = 21050
# def process_csv_files(root_dir, output_csv_path):
#     output_rows = []
#     for root, _, files in os.walk(root_dir):
#         for file in files:
#             if file.endswith('.csv'):
#                 csv_file_path = os.path.join(root, file)
#                 with open(csv_file_path, 'r') as csvfile:
#                     reader = csv.DictReader(csvfile)
#                     for row in reader:
#                         date = row['Date']
#                         time = row['Time']
#                         timestamp_utc = mst_to_utc_with_dst(f"{date} {time}", date_format="%d-%b-%Y")
#                         output_rows.append({'Date': date, 'Time': time, 'Timestamp_UTC': timestamp_utc})
#
#     # Write to a new CSV file
#     with open(output_csv_path, 'w', newline='') as csvfile:
#         fieldnames = ['Date', 'Time', 'Timestamp_UTC']
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(output_rows)
#
#     print(f"Output CSV file has been created at: {output_csv_path}")

def process_csv_files(root_dir, output_csv_path, info_csv_path, pre_window_minutes=10, post_window_minutes=10):
    # List to hold all windows from all files
    all_windows = []

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.csv'):
                print(f'Processing {file}')
                csv_file_path = os.path.join(root, file)
                with open(csv_file_path, 'r') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        date = row['Date']
                        time = row['Time']
                        orig_timestamp = datetime.strptime(f"{date} {time}", "%d-%b-%Y %H:%M:%S")

                        # Calculate start and stop windows
                        start_window = orig_timestamp - timedelta(minutes=pre_window_minutes)
                        stop_window = orig_timestamp + timedelta(minutes=post_window_minutes)

                        all_windows.append({'Start': start_window, 'Stop': stop_window})

    # Sort windows by start time
    all_windows.sort(key=lambda x: x['Start'])

    # Merge overlapping windows
    merged_windows = []
    for window in all_windows:
        if not merged_windows or window['Start'] > merged_windows[-1]['Stop']:
            # No overlap, append the window
            merged_windows.append(window)
        else:
            # There is overlap, update the stop time of the last window
            merged_windows[-1]['Stop'] = max(merged_windows[-1]['Stop'], window['Stop'])

    # Write to a new CSV file
    with open(output_csv_path, 'w', newline='') as csvfile:
        fieldnames = ['Start', 'Stop']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_windows)

    print(f"Output CSV file with windows has been created at: {output_csv_path}")

    # write rows for info_plots
    output_df = pd.DataFrame(
        columns=['Generate', 'AnimalID', 'Sex', 'Kill_ID', 'Start Date', 'Start time', 'End time', 'MarkerTime1', 'MarkerLabel1', 'MarkerTime2', 'MarkerLabel2',	'PlotLabel',	'Labeled Behavior'])

    kill_id = init_kill_id
    for window in merged_windows:
        start_string = window['Start'].strftime("%Y-%m-%d %H:%M:%S")
        stop_string = window['Stop'].strftime("%Y-%m-%d %H:%M:%S")
        start = mst_to_utc_with_dst(start_string)
        stop = mst_to_utc_with_dst(stop_string)
        start_date, start_time = start.split(" ")
        stop_date, stop_time = stop.split(" ")

        # convert date to format expected by info plots
        # Parse the input date string
        date_obj = datetime.strptime(start_date, "%Y-%m-%d")

        # Format the date to the desired format
        start_date = date_obj.strftime("%m/%d/%Y")

        output_df = output_df._append({
            'Generate': 'x',
            'AnimalID': animal_id,
            'Sex': sex,
            'Kill_ID': kill_id,
            'Start Date': start_date,
            'Start time': start_time,
            'End time': stop_time,
            'MarkerTime1': start_time,
            'MarkerLabel1': 'Trailcam Start',
            'MarkerTime2': stop_time,
            'MarkerLabel2': f'Window Stop ({post_window_minutes} mins)',
            'PlotLabel': f'Feeding for {kill_id=}',
            'Labeled Behavior': f'FEED',
        },

            ignore_index=True)
        kill_id += 1
    output_df.to_csv(info_csv_path, index=False)

    print(f"Info Plots CSV file written to: {output_csv_path}")


if __name__ == "__main__":
    root_directory = os.path.join(ROOT_DIR, "data", "trail_cam_csvs", "feeding")
    data_dir = os.path.join(root_directory, "orig")
    output_csv_path = os.path.join(root_directory, "F210_feeding.csv")
    info_csv_path = os.path.join(root_directory, "info_plots.csv")

    pre_window_minutes = 0
    post_window_minutes = 20
    process_csv_files(data_dir, output_csv_path, info_csv_path, pre_window_minutes, post_window_minutes)
