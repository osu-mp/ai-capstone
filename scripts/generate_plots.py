import argparse

import sys
import os

# Get the parent directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))

# Add the parent directory to the system path
sys.path.append(parent_dir)

from utils import data_config
from utils import spreadsheet_utils

def generate_plots():
    parser = argparse.ArgumentParser(description="Generate plots of animal behavior")
    parser.add_argument('--plot_dir', default=data_config.data_paths['plot_root'],
                        help='Optional override to set where plots are generated')
    parser.add_argument('--dry_run', action='store_true', help='Dry run, generate R scripts/batch file but skip generating plots')
    parser.add_argument('--verbose', action='store_true', help='Turn on more debug prints')
    parser.add_argument('--clear_plots', action='store_true', help='Remove everything in the plot dir')
    parser.add_argument('--views', nargs='*', choices=spreadsheet_utils.get_all_view_options(),
                        help='Which time views to plot (choose any number)', default=spreadsheet_utils.get_all_view_options())


    # Add more arguments/options as needed

    args = parser.parse_args()

    dry_run = args.dry_run
    print(f"{dry_run=}")
    print(f"{args.views=}")
    print(f"{args.plot_dir=}")

if __name__ == "__main__":
    generate_plots()