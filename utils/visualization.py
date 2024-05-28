import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings

# Suppress FutureWarning messages
warnings.simplefilter(action='ignore', category=FutureWarning)

from utils.data_config import beh_names, beh_dict

"""
Configuration of vertical lines added to the plots
key = name of var in input config, value = details about displaying the line (color, style, label)
Each line will only be displayed if the value in the input config falls between
"""
marker_lines = {
    'df_stalk_start': {'color': 'orange', 'linestyle': '-', 'label': 'Start Stalk'},
    'ts_kill_start': {'color': 'brown', 'linestyle': '-', 'label': 'Start Kill'},
    'df_kill_end': {'color': 'green', 'linestyle': '--', 'label': 'Kill End Phase1'},
    'df_kill_phase2_end': {'color': 'blue', 'linestyle': '--', 'label': 'Kill End Phase 2'},
    "df_feed_start": {'color': 'magenta', 'linestyle': '-', 'label': 'Start Feed'},
    "df_feed_stop": {'color': 'purple', 'linestyle': '-', 'label': 'Stop Feed'},
    "beh_start": {'color': 'green', 'linestyle': '-', 'label': 'Beh Start'},
    "beh_end": {'color': 'red', 'linestyle': '-', 'label': 'Beh End'},
}


def plot_data(config):
    """
    Use matplotlib to plot the accelerometer data in the given config
    The CSV file with the raw accel data is read, and a PNG is output.
    Only entries between 'time_low' and 'time_high' are displayed (along with any marker lines).
    :param config:
    :return:
    """
    # Load CSV data
    accel = pd.read_csv(config['csv_path'], skiprows=1)

    # Rename columns
    accel = accel.rename(columns={'Acc X [g]': 'X.Axis', 'Acc Y [g]': 'Y.Axis', 'Acc Z [g]': 'Z.Axis'})

    # Format date column
    date_info = datetime(config['year'], config['month'], config['day'], config['hour'], config['window_low_min'], second=0, microsecond=0)

    # Specify the format of the datetime strings
    date_format = "%H:%M:%S"

    accel['UTC DateTime'] = pd.to_datetime(accel['UTC DateTime'], utc=True, format=date_format)
    accel['UTC DateTime'] = accel['UTC DateTime'].apply(lambda x: datetime.combine(date_info, x.time()))

    # Combine date and milliseconds
    accel['UTC DateTime'] += pd.to_timedelta(accel['Milliseconds'], unit='ms')

    # Convert raw accelerometer data to g's
    accel['Xg'] = accel['X.Axis'] * 64 / 1000
    accel['Yg'] = accel['Y.Axis'] * 64 / 1000
    accel['Zg'] = accel['Z.Axis'] * 64 / 1000
    # # Filter data within time boundaries
    while config['window_high_min'] > 59:
        config['window_high_min'] -= 60
        config['hour_high'] += 1

    # Define time boundaries
    time_low = pd.Timestamp(
        datetime(config['year'], config['month'], config['day'], config['hour'], config['window_low_min']) - timedelta(
            minutes=config['window_pre_mins']), second=0, microsecond=0)
    time_high = pd.Timestamp(datetime(config['year'], config['month'], config['day'], config['hour_high'],
                                      config['window_high_min']) + timedelta(minutes=config['window_post_mins']), second=0, microsecond=0)


    # Filter data within time boundaries
    df = accel[
        (pd.to_datetime(accel['UTC DateTime']) >= time_low) & (pd.to_datetime(accel['UTC DateTime']) <= time_high)]

    # Convert infinite values to NaN
    df = df.replace([np.inf, -np.inf], np.nan)

    # Plot
    sns.set_style("whitegrid")
    plt.figure(figsize=(10, 6))
    # Plot X, Y, Z in red, black, blue
    sns.lineplot(data=df, x='UTC DateTime', y='Xg', color='red', label='X Axis', alpha=0.6)
    sns.lineplot(data=df, x='UTC DateTime', y='Yg', color='black', label='Y Axis', alpha=0.5)
    sns.lineplot(data=df, x='UTC DateTime', y='Zg', color='blue', label='Z Axis', alpha=0.7)

    plt.xlabel('Time')
    plt.ylabel('Acceleration (g\'s)')
    title = f"{config['lion_name']} - Kill #{config['Kill_ID']} - {time_low.strftime('%Y-%m-%d')} - {config['plot_type'].capitalize()}"
    plt.title(title)
    plt.ylim(-0.3, 0.3)

    # add any vertical markers that fall into the time window
    for marker in marker_lines:
        if marker not in config:
            continue
        marker_time = config[marker]
        label = marker_lines[marker]['label']
        if marker == "beh_start":
            label = config['marker_1_label']
        elif marker == "beh_end":
            label = config['marker_2_label']

        if marker_time >= time_low and marker_time <= time_high:
            plt.axvline(x=marker_time, color=marker_lines[marker]['color'], linestyle=marker_lines[marker]['linestyle'], label=label),

    # Add legend
    plt.legend()

    # Save plot
    plt.savefig(config['lion_plot_path'])
    # print(f"Generated {config['lion_plot_path']}!")
    plt.close()


def plot_kill_predictions(df, kill_statuses, fname):
    """
    Plot behavior data with status indicators for start of kill behaviors.

    Args:
    df (pd.DataFrame): DataFrame containing behavior data. Assumes a single column named 'behavior'.
    start_times (list): List of start times for kill behaviors.

    Returns:
    None
    """

    # Plotting
    fig, ax = plt.subplots(figsize=(8, 4))

    # Sample data
    time_periods = range(len(df))
    behavior_data = df['behavior'].tolist()

    # find the location of the kill behavior and put markers above it
    kill_marker_index = beh_dict['KILL'] + 0.5

    # Plot behavior data
    for beh_name, beh_value in beh_dict.items():
        y_data = [beh_value if b == beh_value else None for b in behavior_data]
        ax.plot(time_periods, y_data, linewidth=4)

    # # Plot status indicators for start of kill behaviors
    for time, status in kill_statuses.items():
        marker = 'x' if not status else 'P'
        color = 'red' if not status else 'green'
        ax.scatter(time, kill_marker_index, marker=marker, color=color, s=100)

    # Adjusting line height
    num_behaviors = len(beh_dict) / 2.5
    line_height = num_behaviors  # Adjust this value to control the line height
    ax.set_ylim(-line_height, num_behaviors * (line_height))


    # Set y-axis labels
    ax.set_yticks(range(len(beh_names)))
    ax.set_yticklabels(beh_names)

    # Set plot title and labels
    ax.set_title('Behavior Sequence with Kill Status Indicators')
    ax.set_xlabel('Time')
    ax.set_ylabel('Behavior')

    # Create custom legend for '+' and 'X' markers
    ax.scatter([], [], marker='P', color='green', s=100, label='Kill Succeeded')  # Green Plus
    ax.scatter([], [], marker='x', color='red', s=100, label='Kill Failed')  # Red X
    ax.legend()

    # Show plot
    # plt.grid(True)
    plt.tight_layout()  # Adjust layout to remove whitespace

    plt.savefig(fname)
    plt.close()
