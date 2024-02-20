import os
import pandas as pd
from datetime import datetime, timedelta

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
    print(f"Date window for {file_path}: {earliest_date.strftime('%m/%d/%Y')} - {latest_date.strftime('%m/%d/%Y')}")
    
        
    for index, row in df.iterrows():
        # Extracting relevant columns
        animal_id = int(row['ID'][1:])
        sex = row['ID'][0]
        start_date = row['Date'] # datetime.strptime(row['Date'], '%d-%b-%y') # Parse date in "18-Dec-20" format        
        start_time = datetime.strptime(row['Time'], '%H:%M:%S')
        end_time = start_time + timedelta(minutes=10)
        start_time_minus_5 = start_time - timedelta(minutes=5)
        marker_time_1 = start_time
        
        # Generating Kill_ID
        kill_id = output_df['Kill_ID'].max() + 1 if len(output_df) > 0 else 1000        
        # Appending to output dataframe
        output_df = output_df._append({'AnimalID': animal_id,
                                    'Sex': sex,
                                    'Kill_ID': kill_id,
                                    'Start Date': start_date.strftime('%m/%d/%Y'),
                                    'Start time': start_time_minus_5.strftime('%H:%M:%S'),
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