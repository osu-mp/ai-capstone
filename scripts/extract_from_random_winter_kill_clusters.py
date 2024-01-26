import pandas as pd
from datetime import timedelta

# Read the CSV file
df = pd.read_csv('random_winter_kill_clusters.csv')

# Ensure that 'clus_start' is a datetime object
df['clus_start'] = pd.to_datetime(df['clus_start'])

# Extract AnimalID and Sex from cougar_id
df['AnimalID'] = df['cougar_id'].apply(lambda x: x[1:])
df['Sex'] = df['cougar_id'].apply(lambda x: x[0])

# we already have these cats, ignore for now
df = df[~df['AnimalID'].isin(['202', '207', '209'])]

# Calculate Start time and End time
df['Start time'] = df['clus_start'] - timedelta(hours=6)
df['End time'] = df['clus_start'] + timedelta(hours=6)

# Rename columns as required
df.rename(columns={'carcass_id1': 'Kill_ID', 
                   'clus_start': 'Start Date'}, inplace=True)

# Extract the date from Start Date
df['Start Date'] = df['Start Date'].dt.date

# Extract time from Start time and End time
df['Start time'] = df['Start time'].dt.time
df['End time'] = df['End time'].dt.time

# Select only the required columns
df_final = df[['AnimalID', 'Sex', 'Kill_ID', 'Start Date', 'Start time', 'End time']]

# Write to new CSV file
df_final.to_csv('processed_winter_kill_data.csv', index=False)

print("Data processed and saved to processed_winter_kill_data.csv.")
