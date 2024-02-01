import argparse
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import os
from pathlib import Path
import seaborn as sns
import sys
import warnings

"""
Generates kill summary statistics per cat and for all cats for the following intervals:
    Stalking
    Killing
    Delay between killing and feeding
    Feeding

You can have these stats displayed by adding '--show-plots' to your command line. 
    Else the plots will be saved to time_summary.png

Add '--quiet' to the command line to skip printing summary stats (mean, std, etc)
"""
labels = ['StalkTime (s)', 'KillTime (s)', 'WaitFeed (s)', 'FeedTime (s)']

# get the project root as the parent of the parent directory of this file
ROOT_DIR = str(Path(__file__).parent.parent.absolute())
sys.path.append(ROOT_DIR)
from utils.data_config import data_paths, spreadsheets, validate_config, view_configs, is_unix, plot_lines, constants

def replace_inf_with_nan(df):
    # used to quiet pandas warning about copying data from slices of DataFrames
    return df.replace([float('inf'), float('-inf')], float('nan'))


def process_cougars_spreadsheet(file_path, show_plots=False, quiet=False):
    # Read the spreadsheet into a dictionary of DataFrames (one for each tab)
    sheets = pd.read_excel(file_path, sheet_name=None)

    key_name = Path(file_path).name

    # dataframe to aggregate across all cats
    all_cougars_df = pd.DataFrame()
    skipped_cats = []


    # Iterate through the list of cougars
    for cougar_name in spreadsheets[key_name]["tabs"]:
        if cougar_name not in sheets:
             skipped_cats.append(cougar_name)
             continue
        
        # Access the DataFrame corresponding to the current cougar
        cougar_df = sheets[cougar_name]

        # Replace infinite values with NaN
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='use_inf_as_na option is deprecated', category=FutureWarning)
            cougar_df = replace_inf_with_nan(cougar_df)


        # drop entries that do not have a StartKill time
        cougar_df = cougar_df.dropna(subset=['StartKill'])

        # Combine AnimalID and Sex columns
        cougar_df['AnimalID_Sex'] = cougar_df['AnimalID'].astype(str) + '_' + cougar_df['Sex'].astype(str)

        #  Convert time columns to datetime
        time_columns = ['StartStalk', 'StartKill', 'EndCons', 'FeedStart', 'FeedStop']
        for col in time_columns:
            cougar_df[col] = pd.to_datetime(cougar_df[col], format='%H:%M:%S').dt.time

        # Calculate StalkTime, KillTime, WaitFeed, FeedTime
        cougar_df[labels[0]] = (pd.to_datetime(cougar_df['StartKill'], format='%H:%M:%S') -
                                pd.to_datetime(cougar_df['StartStalk'], format='%H:%M:%S')).dt.total_seconds()
        cougar_df[labels[1]] = (pd.to_datetime(cougar_df['EndCons'], format='%H:%M:%S') -
                                pd.to_datetime(cougar_df['StartKill'], format='%H:%M:%S')).dt.total_seconds()
        cougar_df[labels[2]] = (pd.to_datetime(cougar_df['FeedStart'], format='%H:%M:%S') -
                                pd.to_datetime(cougar_df['EndCons'], format='%H:%M:%S')).dt.total_seconds()
        cougar_df[labels[3]] = (pd.to_datetime(cougar_df['FeedStop'], format='%H:%M:%S') -
                                pd.to_datetime(cougar_df['FeedStart'], format='%H:%M:%S')).dt.total_seconds()

        # Replace infinite values with NaN
        cougar_df = replace_inf_with_nan(cougar_df)


        # Display summary statistics for each cougar
        if not quiet:
            print(f"\nSummary Statistics for {cougar_name}:")
            summary_stats = cougar_df[labels].describe().round(1)
            print(summary_stats)

        # Plot histograms for each time category
        plt.figure(figsize=(12, 8))
        for i, col in enumerate(labels):
            plt.subplot(2, 2, i + 1)
            with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', message='use_inf_as_na option is deprecated', category=FutureWarning)
                    sns.histplot(cougar_df[col], kde=True)
            plt.title(f'Histogram of {col} for {cougar_name}')
            plt.xlabel(col)
            plt.ylabel('Frequency')

        plt.tight_layout()
        if show_plots:
             plt.show()
        else:
            plot_fname = os.path.join(data_paths['plot_root'], cougar_name, f"{cougar_name}_time_summary.png")
            plt.savefig(plot_fname)
            print(f"Plot saved to {os.path.abspath(plot_fname)}")

        # Append the current cougar's DataFrame to the overall DataFrame
        all_cougars_df = pd.concat([all_cougars_df, cougar_df]).reset_index(drop=True)  # Reset index

    # Replace infinite values with NaN in the combined DataFrame
    all_cougars_df = replace_inf_with_nan(all_cougars_df)

    # Display summary statistics for all cougars combined
    if not quiet:
        print("\nSummary Statistics for All Cougars Combined:")
        all_summary_stats = all_cougars_df[labels].describe().round(0)
        print(all_summary_stats)

    # Plot histograms for each time category for all cougars combined
    plt.figure(figsize=(12, 8))
    for i, col in enumerate([labels]):
        plt.subplot(2, 2, i + 1)
        with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='use_inf_as_na option is deprecated', category=FutureWarning)
                sns.histplot(all_cougars_df[col], kde=True)
        plt.title(f'Histogram of {col} for All Cougars')
        plt.xlabel(col)
        plt.ylabel('Frequency')

    plt.tight_layout()
    if show_plots:
            plt.show()
    else:
        plot_fname = os.path.join(data_paths['plot_root'], "time_summary.png")
        plt.savefig(plot_fname)
        print(f"Plot saved to {os.path.abspath(plot_fname)}")

    if skipped_cats:
         print(f"\nWARNING: The following cats were in the config but not in the spreadsheet: {' '.join(skipped_cats)}")
    
def main():
    parser = argparse.ArgumentParser(description='Process Cougar spreadsheet and display/save plots.')
    parser.add_argument('--show-plots', action='store_true', help='Display plots instead of saving to file')
    parser.add_argument('--quiet', action='store_true', help='Omit summary printouts')

    args = parser.parse_args()

    data_root = data_paths['spreadsheet_root']
    for spreadsheet in spreadsheets:            
        spreadsheet_path = os.path.join(data_root, spreadsheet)

        # Make sure the file exists
        if os.path.exists(spreadsheet_path):
            process_cougars_spreadsheet(spreadsheet_path, show_plots=args.show_plots, quiet=args.quiet)
        else:
            print(f"The file '{spreadsheet_path}' does not exist, skipping")


if __name__ == "__main__":
    main()