from collections import defaultdict
from datetime import datetime
import glob
import math
import os
import pandas as pd
from PIL import Image
import subprocess
import time

from utils.data_config import data_paths, spreadsheets, validate_config, view_configs, is_unix

# TODO: use logger

# TODO: combine multiple plots into one image

# TODO: make command line args

# TODO: make yellow transpare
launch = True
verbose = False
clear_plot_dir = False

def identify_kills():
    """
    Iterate over all spreadsheets/tabs and generate a config dict
    for each data window of interest.
    :return:
    """
    configs = []
    expected_plots = set()
    spreadsheet_root = os.path.abspath(data_paths["spreadsheet_root"])
    plot_root = data_paths["plot_root"]
    missing_csvs = set()
    plot_counts = defaultdict(int)

    for spreadsheet in spreadsheets:
        path = os.path.join(spreadsheet_root, spreadsheet)
        print(f"Processing spreadsheet {path}")
        df_all = pd.DataFrame()
        with pd.ExcelFile(path) as f:
            sheets = f.sheet_names
            if "tabs" in spreadsheets[spreadsheet]:
                cfg_sheets = spreadsheets[spreadsheet]["tabs"]
                if sheets != cfg_sheets:
                    print("INFO: You are using a subset of the sheets in the spreadsheet:")
                    print(f"\tSheets in file: {sorted(sheets)}")
                    print(f"\tSheets in cfg:  {sorted(cfg_sheets)}")
            else:
                cfg_sheets = f.sheet_names

            tab_skipped = False
            for sheet in cfg_sheets:
                df = f.parse(sheet)
                cols = spreadsheets[spreadsheet]['data_cols']
                if not all(column in df.columns for column in cols):
                    print(f"WARNING: Missing columns in tab {sheet}, no data read from there.")
                    tab_skipped = True
                    continue
                df = df[cols]
                df = df[df['Period'] == 'Kill']
                df["data_root"] = spreadsheets[spreadsheet]["tabs"][sheet]
                df_all = pd.concat([df_all, df], ignore_index=True)

        if tab_skipped:
            print(f"Some tabs skipped because of bad data. Expected columns: {', '.join(cols)}")
        if verbose:
            print(f"ALL {df_all}")

    no_id_kill_index = 9999
    for index, row in df_all.iterrows():
        year = row['Start Date'].year
        month = row['Start Date'].month
        day = row['Start Date'].day
        hour = row['Start time'].hour
        window_low_min = row['Start time'].minute
        window_high_min = row['End Time'].minute
        window_high_min = max(window_low_min + 1, window_high_min)      # ensure the window is at least 1 minute

        plot_date = datetime(year=year, month=month, day=day, hour=hour, minute=window_low_min)

        kill_id = row['Kill_ID']
        if math.isnan(kill_id):
            kill_id = no_id_kill_index
            no_id_kill_index += 1
        else:
            kill_id = int(kill_id)

        lion_id = f"{row['Sex']}{int(row['AnimalID'])}"
        lion_plot_root = os.path.join(plot_root, lion_id)
        if not os.path.isdir(lion_plot_root):
            os.makedirs(lion_plot_root)
        plot_name = plot_date.strftime(f"{lion_id}_%Y-%m-%d__%H_%M__{kill_id}")  # the R script will append config type/kill id and .png
        lion_plot_path = os.path.join(lion_plot_root, plot_name)

        csv_folder = plot_date.strftime("%Y/%m %b/%d/")
        csv_name = plot_date.strftime("%Y-%m-%d.csv")
        csv_path = os.path.join(row["data_root"], csv_folder, csv_name)
        csv_path = csv_path.replace("\\", "/")      # R does not like backward slashes, convert to forward
        if not os.path.isfile(csv_path):
            missing_csvs.add(csv_path)
            continue

        expected_plots.add(plot_name)

        plot_counts[lion_id] += 1
        data = {
            "lion_name": f"{lion_id}",
            "window_low_min": window_low_min,
            "window_high_min": window_high_min,
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "Kill_ID": kill_id,
            "lion_plot_path": lion_plot_path,
            "csv_path": csv_path
        }
        configs.append(data)
        # expected_plots.add(data["lion_plot_path"])

    if missing_csvs:
        print(f"WARNING: The following {len(missing_csvs)} CSVs were missing, will not be processed:")
        for csv in missing_csvs:
            print(f"\t{csv}")

    print("\nWe plan on generating this many plots per cat:")
    for key, value in plot_counts.items():
        print(f"\t{key}: {value * len(view_configs)}")
    return configs, expected_plots


def generate_scripts(configs, expected_plots):
    """
    For each config generated from the spreadhsheet data, generate
    an R script to extract the data.
    Generate a batch file that will run contain all generated scripts.
    :param configs:
    :return:
    """
    template_path = os.path.abspath(data_paths["template_path"])
    output_path = os.path.abspath(data_paths["output_path"])
    r_path = os.path.abspath(data_paths["r_path"])
    batch_fname = os.path.join(output_path, "run_batch.bat")
    if is_unix:
        batch_fname = os.path.join(output_path, "run.csh")
    all_expected_plots = set()

    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    generated_files = []
    for config in configs:
        for key, value in view_configs.items():
            config["plot_type"] = key
            config["window_pre_mins"] = value["window_pre_mins"]
            config["window_post_mins"] = value["window_post_mins"]
            config["minor_tick_interval"] = value["minor_tick_interval"]
            filled_template = template_content.format(**config)
            filled_template = filled_template.replace("\\", "/")

            out_fname = os.path.join(output_path, f"script_{config['lion_name']}_{config['plot_type']}_{config['Kill_ID']}.r")
            with open(out_fname, "w") as output_file:
                output_file.write(filled_template)
            if verbose:
                print(f"Generated {out_fname}")
            generated_files.append(out_fname)

    batch_path = os.path.abspath(batch_fname)
    with open(batch_path, "w") as output_file:
        if is_unix:
            output_file.write("#!/usr/bin/bash\n\n")
        else:
            output_file.write("@echo off\n\n")

        for fname in generated_files:
            if is_unix:
                output_file.write(f"{r_path} {fname} > {fname}.log 2>&1\n")
            else:
                output_file.write(f"\"{r_path}\" \"{fname}\" > \"{fname}.log\" 2>&1\n")

    print(f"\nGenerated {len(generated_files)} files in {batch_path}")

    for expected_plot in expected_plots:
        for key in view_configs.keys():
            all_expected_plots.add(f"{expected_plot}_{key}")

    # make the file executable
    os.chmod(batch_path, 0o755)

    return batch_path, all_expected_plots

def get_all_view_options():
     # return a list of all valid views, used by command line parser
    return list(view_configs.keys())

def combine_images(path1, path2, path3, new_name):
    for path in [path1, path2, path3]:
        if not os.path.isfile(path):
            print(f"Unable to combine images due to missing {path}")
            return

    # Load your three PNG images
    image1 = Image.open(path1)
    image2 = Image.open(path2)
    image3 = Image.open(path3)

    # Assuming all images have the same height, adjust if not
    total_height = image1.height

    # Calculate the width for the combined image
    total_width = sum([img.width for img in [image1, image2, image3]])

    # Create a new blank image with the calculated dimensions
    combined_image = Image.new("RGB", (total_width, total_height))

    # Paste the individual images into the combined image, arranging them in columns
    x_offset = 0
    for img in [image1, image2, image3]:
        combined_image.paste(img, (x_offset, 0))
        x_offset += img.width

    # Save the combined image
    combined_image.save(new_name)
    print(f"Generated {new_name=}")

def make_mega_plots(root, expected_plots):
    """
    If we have a labeling plot, attempt to make a larger image of the sequence:
        stalking, labeling, feeding
    This allows for a quick view at different levels
    :param root:
    :param expected_plots:
    :return:
    """
    # hardcoded BS here
    generated_plots = glob.glob(os.path.join(data_paths["plot_root"], "*/*.png"))
    for plot in generated_plots:
        if 'labeling' in plot:
            path1 = plot.replace('labeling', 'stalking')
            path2 = plot
            path3 = plot.replace('labeling', 'feeding')
            new_name = plot.replace('labeling', 'mega')
            combine_images(path1, path2, path3, new_name)

if __name__ == '__main__':
    validate_config()
    configs, expected_plots = identify_kills()
    batch_file, expected_plots = generate_scripts(configs, expected_plots)

    if launch:
        if clear_plot_dir:
            plot_root = data_paths["plot_root"]
            print(f"Clearing PNG files from plot dir: {plot_root}")
            file_pattern = os.path.join(plot_root, '*/*.png')  # Example: Remove all txt files
            files_to_remove = glob.glob(file_pattern)
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
                except OSError as e:
                    print(f"Error removing file {file_path}: {e}")
        print(f"Launching {batch_file} (this may take awhile)")
        print("Results from each script will be written to <script>.log")
        start = time.time()
        subprocess.run([batch_file])
        runtime = time.time() - start
        print(f"Runtime: {runtime:3.0f} seconds")
        print(f"Average time per run: {runtime/len(expected_plots):2.2f} seconds")

        make_mega_plots(data_paths["plot_root"], expected_plots)

        # check expected plots
        generated_plots = glob.glob(os.path.join(data_paths["plot_root"], "*/*.png"))
        for plot in list(expected_plots):
            for generated_plot in generated_plots:
                if plot in generated_plot:
                    expected_plots.remove(plot)
                    break

        if expected_plots:
            print(f"The following {len(expected_plots)} plots were expected but not found:")
            for plot in expected_plots:
                print(f"\t{plot}")
        else:
            print("SUCCESS: All expected plots appear to be generated!")


