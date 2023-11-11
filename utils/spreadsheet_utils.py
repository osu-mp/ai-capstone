import math
import os
import subprocess
import pandas as pd

from data_config import data_paths, spreadsheets, validate_config, view_configs

launch = False
verbose = False


def identify_kills():
    """
    Iterate over all spreadsheets/tabs and generate a config dict
    for each data window of interest.
    :return:
    """
    configs = []
    spreadsheet_root = os.path.abspath(data_paths["spreadsheet_root"])
    plot_root = data_paths["plot_root"]

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

        kill_id = row['Kill_ID']
        if math.isnan(kill_id):
            kill_id = no_id_kill_index
            no_id_kill_index += 1
        else:
            kill_id = int(kill_id)

        lion_id = f"{row['Sex']}{row['AnimalID']}"
        lion_plot_root = os.path.join(plot_root, lion_id)
        if not os.path.isdir(lion_plot_root):
            os.makedirs(lion_plot_root)
        data = {
            "lion_name": f"{lion_id}",
            "window_low_min": window_low_min,
            "window_high_min": window_high_min,
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "Kill_ID": kill_id,
            "lion_plot_root": lion_plot_root
        }
        configs.append(data)

    return configs


def generate_scripts(configs):
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

    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    generated_files = []
    for config in configs:
        for key, value in view_configs.items():
            config["plot_type"] = key
            config["window_pre_mins"] = value["window_pre_mins"]
            config["window_post_mins"] = value["window_post_mins"]
            filled_template = template_content.format(**config)

            out_fname = os.path.join(output_path, f"script_{config['lion_name']}_{config['plot_type']}_{config['Kill_ID']}.r")
            with open(out_fname, "w") as output_file:
                output_file.write(filled_template)
            if verbose:
                print(f"Generated {out_fname}")
            generated_files.append(out_fname)

    batch_path = os.path.abspath(batch_fname)
    with open(batch_path, "w") as output_file:
        output_file.write("@echo off\n\n")
        for fname in generated_files:
            output_file.write(f"\"{r_path}\" \"{fname}\" > \"{fname}.log\" 2>&1\n")

    print(f"\nGenerated {len(generated_files)} files in {batch_path}")

    return batch_path


if __name__ == '__main__':
    validate_config()
    configs = identify_kills()
    batch_file = generate_scripts(configs)
    if launch:
        print(f"Launching {batch_file} (this may take awhile)")
        print("Results from each script will be written to <script>.log")
        subprocess.run([batch_file])
