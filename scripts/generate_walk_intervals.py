import os
import pandas as pd
from datetime import datetime, timedelta

HOUR_OFFSET = -7         # number of hours to add to account for timezone difference
WINDOW_MINS = 10        # number of minutes on either side of window to show

# Get the parent directory of the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Input and output directories
input_dir = os.path.join(project_root, 'data', 'trail_cam_csvs')
output_file = os.path.join(project_root, 'data', 'trail_cam_walks.csv')

# Function to process each CSV file
def process_csv(file_path, output_df):
    df = pd.read_csv(file_path)

    # Convert Date column to datetime format
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    
    # Extracting the earliest and latest dates
    earliest_date = df['Date'].min()
    latest_date = df['Date'].max()
    
    # Print date window
    print(f"Date window for {os.path.basename(file_path)}: {earliest_date.strftime('%m/%d/%Y')} - {latest_date.strftime('%m/%d/%Y')}")
    
        
    for index, row in df.iterrows():
        # Extracting relevant columns
        animal_id = int(row['ID'][1:])
        sex = row['ID'][0]
        start_date = row['Date']
        start_time = datetime.strptime(row['Time'], '%H:%M:%S')
        # check if the previous or next day is needed
        if HOUR_OFFSET < 0 and start_time.hour < abs(HOUR_OFFSET):
            start_date -= timedelta(hours=24)
        elif HOUR_OFFSET > 0 and start_time.hour > 24 - HOUR_OFFSET:
            start_date += timedelta(hours=24)
        start_time += timedelta(hours=HOUR_OFFSET)        
        end_time = start_time + timedelta(minutes=WINDOW_MINS)
        start_time_window = start_time - timedelta(minutes=WINDOW_MINS)
        marker_time_1 = start_time
        
        # Generating Kill_ID
        kill_id = output_df['Kill_ID'].max() + 1 if len(output_df) > 0 else 1000        
        output_df = output_df._append({'AnimalID': animal_id,
                                    'Sex': sex,
                                    'Kill_ID': kill_id,
                                    'Start Date': start_date.strftime('%m/%d/%Y'),
                                    'Start time': start_time_window.strftime('%H:%M:%S'),
                                    'End time': end_time.strftime('%H:%M:%S'),
                                    'MarkerTime1': marker_time_1.strftime('%H:%M:%S')}, 
                                    ignore_index=True)
    
    return output_df

# Iterate over all CSV files in the input directory
output_df = pd.DataFrame(columns=['AnimalID', 'Sex', 'Kill_ID', 'Start Date', 'Start time', 'End time', 'MarkerTime1'])
for file_name in os.listdir(input_dir):
    if file_name.endswith('.csv'):
        file_path = os.path.join(input_dir, file_name)
        output_df = process_csv(file_path, output_df)

# Writing to output CSV
output_df.to_csv(output_file, index=False)
print(f"Collated entries into {output_file}")