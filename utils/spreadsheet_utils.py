from collections import defaultdict
import concurrent.futures
from datetime import datetime, timedelta
import glob
import math
import multiprocessing
import os
import pandas as pd
from pathlib import Path
from PIL import Image
import shutil
import subprocess
import sys
import time

# get the project root as the parent of the parent directory of this file
ROOT_DIR = str(Path(__file__).parent.parent.absolute())
sys.path.append(ROOT_DIR)
from utils.data_config import data_paths, spreadsheets, validate_config, view_configs, is_unix, plot_lines

# TODO: use logger
# TODO: make command line args

# TODO: make yellow transpare
launch = True
verbose = False
clear_plot_dir = True
create_csvs = True


def dump_tab(xls_path, sheet_name):
    # Get the current date
    current_date = datetime.now()

    # Format the date as year_month_date
    formatted_date = current_date.strftime("%Y_%m_%d")

    root_dir = os.path.join(data_paths["csv_backup"], formatted_date)
    os.makedirs(root_dir, exist_ok=True)

    csv_path = os.path.join(root_dir, f"{sheet_name}.csv")

    df = pd.read_excel(xls_path, sheet_name=sheet_name)
    df.to_csv(csv_path, index=False)
    print(f"Created {csv_path=}")

def get_lion_plot_window_dir(lion_id, main=False):
    """
    Return the path where the sub plots (individual windows) for the given lion are expected
    Make the dir if it does not exist
    """
    plot_root = data_paths["plot_root"]
    lion_plot_root = os.path.join(plot_root, lion_id)
    if not main:
        lion_plot_root = os.path.join(lion_plot_root, "windows")
    if not os.path.isdir(lion_plot_root):
        os.makedirs(lion_plot_root)

    return lion_plot_root

def create_data_from_row(row, missing_csvs, expected_plots, plot_counts):
    year = row['Start Date'].year
    month = row['Start Date'].month
    day = row['Start Date'].day
    hour = row['Start time'].hour
    window_low_min = row['Start time'].minute
    window_high_min = row['End Time'].minute
    window_high_min = max(window_low_min + 1, window_high_min)      # ensure the window is at least 1 minute

    if 'StartKill' not in row or pd.isnull(row['StartKill']):
        return None

    cons_window_low_hour = row['StartKill'].hour
    cons_window_low_min = row['StartKill'].minute
    cons_window_low_sec = row['StartKill'].second
    cons_window_high_hour = row['EndCons'].hour
    cons_window_high_min = row['EndCons'].minute
    cons_window_high_sec = row['EndCons'].second

    lib_window_low_hour = cons_window_low_hour# row['StartLib'].hour
    lib_window_low_min = cons_window_low_min # row['StartLib'].minute
    lib_window_low_sec = cons_window_low_sec # row['StartLib'].second
    lib_window_high_hour = row['EndLib'].hour
    lib_window_high_min = row['EndLib'].minute
    lib_window_high_sec = row['EndLib'].second
   
    stalk_start_hour = row['StartStalk'].hour
    stalk_start_min = row['StartStalk'].minute
    stalk_start_sec = row['StartStalk'].second

    feed_start_hour = row['FeedStart'].hour
    feed_start_min = row['FeedStart'].minute
    feed_start_sec = row['FeedStart'].second
    feed_stop_hour = row['FeedStop'].hour
    feed_stop_min = row['FeedStop'].minute
    feed_stop_sec = row['FeedStop'].second
    

    plot_date = datetime(year=year, month=month, day=day, hour=hour, minute=window_low_min)

    # csv related
    # TODO: stalk window, kill start, phase1, phase2  

    kill_id = row['Kill_ID']
    # if kill_id != 940:          # TODO Debug get rid of
    #     continue
    if math.isnan(kill_id):
        kill_id = no_id_kill_index
        no_id_kill_index += 1
    else:
        kill_id = int(kill_id)

    lion_id = f"{row['Sex']}{int(row['AnimalID'])}"
    lion_plot_root = get_lion_plot_window_dir(lion_id)    
    plot_name = plot_date.strftime(f"{lion_id}_%Y-%m-%d__%H_%M__{kill_id}")  # the R script will append config type/kill id and .png
    lion_plot_path = os.path.join(lion_plot_root, plot_name)

    csv_folder = plot_date.strftime("%Y/%m %b/%d/")
    csv_name = plot_date.strftime("%Y-%m-%d.csv")
    csv_path = os.path.join(row["data_root"], csv_folder, csv_name)
    csv_path = csv_path.replace("\\", "/")      # R does not like backward slashes, convert to forward
    if not os.path.isfile(csv_path):
        missing_csvs.add(csv_path)
        return None

    expected_plots.add(plot_name)

    plot_counts[lion_id] += 1
    data = {
        "lion_name": f"{lion_id}",
        "lion_id": lion_id,
        "window_low_min": window_low_min,
        "window_high_min": window_high_min,
        # TODO : can this be simplified?
        "cons_window_low_hour": cons_window_low_hour,
        "cons_window_low_min": cons_window_low_min,
        "cons_window_low_sec": cons_window_low_sec,
        "cons_window_high_hour": cons_window_high_hour,
        "cons_window_high_min": cons_window_high_min,
        "cons_window_high_sec": cons_window_high_sec,
        # TODO
        "lib_window_low_hour": lib_window_low_hour,
        "lib_window_low_min": lib_window_low_min,
        "lib_window_low_sec": lib_window_low_sec,
        "lib_window_high_hour": lib_window_high_hour,
        "lib_window_high_min": lib_window_high_min,
        "lib_window_high_sec": lib_window_high_sec,
        # TODO
        "stalk_start_hour": stalk_start_hour,
        "stalk_start_min": stalk_start_min,
        "stalk_start_sec": stalk_start_sec,
        "feed_start_hour": feed_start_hour,
        "feed_start_min": feed_start_min,
        "feed_start_sec": feed_start_sec,
        "feed_stop_hour": feed_stop_hour,
        "feed_stop_min": feed_stop_min,
        "feed_stop_sec": feed_stop_sec,
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "Kill_ID": kill_id,
        "lion_plot_path": lion_plot_path,
        "csv_path": csv_path,

        "marker_1_hour": 0,
        "marker_1_min": 0,
        "marker_1_sec": 0,
        "marker_1_label": 0,   
        # TODO
        "marker_2_hour": 0,
        "marker_2_min": 0,
        "marker_2_sec": 0,
        "marker_2_label": 0, 

        "marker_info": get_marker_info(info_plot=False),
        "is_sixhour": "FALSE",
        # timestamps
        "ts_kill_start": datetime(year, month, day, cons_window_low_hour, cons_window_low_min, cons_window_low_sec),
        # dataframe timestamps, used for behavior classification
        "df_stalk_start": pd.Timestamp(pd.Timestamp(year, month, day, stalk_start_hour, stalk_start_min, stalk_start_sec).strftime("%I:%M:%S %p")),
        "df_stalk_end": pd.Timestamp(pd.Timestamp(year, month, day, cons_window_low_hour, cons_window_low_min, cons_window_low_sec).strftime("%I:%M:%S %p")),
        "df_kill_start": pd.Timestamp(pd.Timestamp(year, month, day, cons_window_low_hour, cons_window_low_min, cons_window_low_sec).strftime("%I:%M:%S %p")),
        "df_kill_end": pd.Timestamp(pd.Timestamp(year, month, day, cons_window_high_hour, cons_window_high_min, cons_window_high_sec).strftime("%I:%M:%S %p")),
        "df_feed_start": pd.Timestamp(pd.Timestamp(year, month, day, feed_start_hour, feed_start_min, feed_start_sec).strftime("%I:%M:%S %p")),
        "df_feed_stop": pd.Timestamp(pd.Timestamp(year, month, day, feed_stop_hour, feed_stop_min, feed_stop_sec).strftime("%I:%M:%S %p")),
    }

    return data
def identify_kills():
    """
    Iterate over all spreadsheets/tabs and generate a config dict
    for each data window of interest.
    :return:
    """
    configs = []
    expected_plots = set()
    spreadsheet_root = os.path.abspath(data_paths["spreadsheet_root"])
    
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
                dump_tab(path, sheet)
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
        try:
            data = create_data_from_row(row, missing_csvs, expected_plots, plot_counts)
            if data:
                configs.append(data)
        except Exception as e:
            # print(f"Ignoring row {row}")
            print(f"Invalid row for animal of {row['AnimalID']}, kill of {row['Kill_ID']}: {e}")
        # expected_plots.add(data["lion_plot_path"])

    if missing_csvs:
        print(f"WARNING: The following {len(missing_csvs)} CSVs were missing, will not be processed:")
        for csv in missing_csvs:
            print(f"\t{csv}")

    print("\nWe plan on generating this many plots per cat:")
    for key, value in plot_counts.items():
        print(f"\t{key}: {value * len(view_configs)}")
    return configs, expected_plots

    
def get_plot_info_entries():
    """
    Iterate over all entries in the info tab
    for each data window of interest.
    :return:
    """
    configs = []
    expected_plots = set()
    spreadsheet_root = os.path.abspath(data_paths["spreadsheet_root"])
    missing_csvs = set()
    plot_counts = defaultdict(int)
    generated_files = []
    template_path = os.path.abspath(data_paths["template_path"])
    output_path = os.path.abspath(data_paths["output_path"])

    for spreadsheet in spreadsheets:
        path = os.path.join(spreadsheet_root, spreadsheet)
        print(f"Processing spreadsheet {path}")
        df_all = pd.DataFrame()
        with pd.ExcelFile(path) as f:
            sheets = f.sheet_names
            if 'InfoPlots' not in sheets:
                print("No InfoPlots tab, skipping")
                continue
            sheet = 'InfoPlots'
            
            dump_tab(path, sheet)
            df = f.parse(sheet)
            cols = spreadsheets[spreadsheet]['data_cols_info']
            if not all(column in df.columns for column in cols):
                print(f"WARNING: Missing columns in tab {sheet}, no data read from there.")
                continue
            df = df[cols]
            # TODO 
            # df["data_root"] = spreadsheets[spreadsheet]["tabs"][sheet]
            df_all = pd.concat([df_all, df], ignore_index=True)


    for index, row in df_all.iterrows():
        year = row['Start Date'].year
        month = row['Start Date'].month
        day = row['Start Date'].day
        hour = row['Start time'].hour
        window_low_min = row['Start time'].minute
        window_high_min = row['End time'].minute
        window_high_min = max(window_low_min + 1, window_high_min)      # ensure the window is at least 1 minute

        # if 'StartKill' not in row or pd.isnull(row['StartKill']):
        #     continue

        if not pd.isnull(row['MarkerTime1']):
            marker_1_hour = row['MarkerTime1'].hour
            marker_1_min = row['MarkerTime1'].minute
            marker_1_sec = row['MarkerTime1'].second
            marker_1_label = row['MarkerLabel1']
        else:
            marker_1_hour = marker_1_min = marker_1_sec = 0
            marker_1_label = "Unused"

        if not pd.isnull(row['MarkerTime2']):
            marker_2_hour = row['MarkerTime2'].hour
            marker_2_min = row['MarkerTime2'].minute
            marker_2_sec = row['MarkerTime2'].second
            marker_2_label = row['MarkerLabel2']
        else:
            marker_2_hour = marker_2_min = marker_2_sec = 0
            marker_2_label = "Unused"

        plot_label = row['PlotLabel']
        plot_label = plot_label.replace(' ', '_')


        plot_date = datetime(year=year, month=month, day=day, hour=hour, minute=window_low_min)

        kill_id = row['Kill_ID']
        # if kill_id != 940:          # TODO Debug get rid of
        #     continue
        # if math.isnan(kill_id):
        #     kill_id = no_id_kill_index
        #     no_id_kill_index += 1
        # else:
        #     kill_id = int(kill_id)

        lion_id = f"{row['Sex']}{int(row['AnimalID'])}"
        lion_plot_root = get_lion_plot_window_dir(lion_id, main=True)        
        plot_name = plot_date.strftime(f"{lion_id}_%Y-%m-%d__%H_%M__{kill_id}__{plot_label}")  # the R script will append config type/kill id and .png
        lion_plot_path = os.path.join(lion_plot_root, plot_name)

        csv_folder = plot_date.strftime("%Y/%m %b/%d/")
        csv_name = plot_date.strftime("%Y-%m-%d.csv")
        data_root = spreadsheets[spreadsheet]["tabs"][lion_id]
        csv_path = os.path.join(data_root, csv_folder, csv_name)
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
            "info_view": True,
            # TODO : can this be simplified?
            "cons_window_low_hour": 0, #cons_window_low_hour,
            "cons_window_low_min": 0, #cons_window_low_min,
            "cons_window_low_sec": 0, #cons_window_low_sec,
            "cons_window_high_hour": 0, #cons_window_high_hour,
            "cons_window_high_min": 0, #cons_window_high_min,
            "cons_window_high_sec": 0, #cons_window_high_sec,
            # TODO
            "lib_window_low_hour": 0, #lib_window_low_hour,
            "lib_window_low_min": 0, #lib_window_low_min,
            "lib_window_low_sec": 0, #lib_window_low_sec,
            "lib_window_high_hour":0, # lib_window_high_hour,
            "lib_window_high_min": 0, #lib_window_high_min,
            "lib_window_high_sec": 0, #lib_window_high_sec,
            # TODO
            "stalk_start_hour": 0, #stalk_start_hour,
            "stalk_start_min": 0, #stalk_start_min,
            "stalk_start_sec": 0, #stalk_start_sec,
            "feed_start_hour": 0,
            "feed_start_min": 0,
            "feed_start_sec": 0,
            "feed_stop_hour": 0,
            "feed_stop_min": 0,
            "feed_stop_sec": 0,
            # TODO
            "marker_1_hour": marker_1_hour,
            "marker_1_min": marker_1_min,
            "marker_1_sec": marker_1_sec,
            "marker_1_label": marker_1_label,   
            # TODO
            "marker_2_hour": marker_2_hour,
            "marker_2_min": marker_2_min,
            "marker_2_sec": marker_2_sec,
            "marker_2_label": marker_2_label,           

            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "Kill_ID": kill_id,
            "lion_plot_path": lion_plot_path,
            "csv_path": csv_path,

            "marker_info": get_marker_info(info_plot=True, marker_1_label=marker_1_label, marker_2_label=marker_2_label),
            "is_sixhour": "FALSE",
        }
        # configs.append(data)
        # expected_plots.add(data["lion_plot_path"])

    # if missing_csvs:
    #     print(f"WARNING: The following {len(missing_csvs)} CSVs were missing, will not be processed:")
    #     for csv in missing_csvs:
    #         print(f"\t{csv}")

    # print("\nWe plan on generating this many plots per cat:")
    # for key, value in plot_counts.items():
    #     print(f"\t{key}: {value * len(view_configs)}")
    
    
        
        with open(template_path, "r") as template_file:
            template_content = template_file.read()

        # for config in configs:
        #     # for key, value in view_configs.items():
            data["plot_type"] = f"{lion_id} {plot_label}"
            data["window_pre_mins"] = 0# value["window_pre_mins"]
            data["window_post_mins"] = 0# value["window_post_mins"]
            data["minor_tick_interval"] = 10 # TODO value["minor_tick_interval"]
            filled_template = template_content.format(**data)
            filled_template = filled_template.replace("\\", "/")

            out_fname = os.path.join(output_path, f"script_{data['lion_name']}_{data['plot_type']}_{data['Kill_ID']}_{plot_label}.r")
            with open(out_fname, "w") as output_file:
                output_file.write(filled_template)
            if verbose:
                print(f"Generated {out_fname}")
            generated_files.append(out_fname)

    print(f"\nGenerated {len(generated_files)} commands")

    
    # for expected_plot in expected_plots:
    #     for key in view_configs.keys():
    #         all_expected_plots.add(f"{expected_plot}_{key}")

    return generated_files, expected_plots


def get_vline_info(key_name, legend_title):
    lines = []
    values = []
    labels = []
    line_types = []
    colors = []

    for line_dict in plot_lines[key_name]:
            line_text = f'''  geom_vline(
    data = data.frame(xpos = c({line_dict["value"]}), label = c("{line_dict["label"]}")),
    aes(xintercept = as.numeric(xpos), linetype = "{line_dict["label"]}"),
    color = "{line_dict["color"]}", alpha = {line_dict["alpha"]}) +
'''         
            lines.append(line_text)
            values.append(f"\"{line_dict['label']}\" = \"{line_dict['linetype']}\"")
            labels.append(f"\"{line_dict['label']}\"")
            line_types.append(f"\"{line_dict['linetype']}\"")
            colors.append(f"\"{line_dict['color']}\"")    

    r_lines = "\n".join(lines)
    r_values = ", ".join(values)
    r_labels = ", ".join(labels)
    r_linetypes = ", ".join(line_types)
    r_colors = ", ".join(colors)
    r_code = f'''p <- p +
    {r_lines}         scale_linetype_manual(
name = "{legend_title}",
values = c({r_values}),
labels = c({r_labels}),
guide = guide_legend(
    override.aes = list(
    linetype = c({r_linetypes}),
    color = c({r_colors})
    )
)
) 
    '''
    return r_code
    

def get_marker_info(info_plot=False, marker_1_label="Marker1", marker_2_label="Marker2"):
    if info_plot:
        info_str = get_vline_info("info_plot", "Times of Interest")
        info_str = info_str.format(marker_1_label=marker_1_label, marker_2_label=marker_2_label)
        return info_str
    else:
        return get_vline_info("default", "Surge Windows")



def run_r_script(script_name):
    """
    Launch R script, save output to name of script + .log
    """
    output_file = f"{script_name}.log"
    r_path = os.path.abspath(data_paths["r_path"])
    with open(output_file, 'w') as f:
        subprocess.run([r_path, script_name], stdout=f, stderr=subprocess.STDOUT, check=True)
    

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
            config["is_sixhour"] = str(key == "sixhour").upper()
            filled_template = template_content.format(**config)
            filled_template = filled_template.replace("\\", "/")

            out_fname = os.path.join(output_path, f"script_{config['lion_name']}_{config['plot_type']}_{config['Kill_ID']}.r")
            with open(out_fname, "w") as output_file:
                output_file.write(filled_template)
            if verbose:
                print(f"Generated {out_fname}")
            generated_files.append(out_fname)

    print(f"\nGenerated {len(generated_files)} commands")

    
    for expected_plot in expected_plots:
        for key in view_configs.keys():
            all_expected_plots.add(f"{expected_plot}_{key}")

    return generated_files, all_expected_plots

def get_all_view_options():
     # return a list of all valid views, used by command line parser
    return list(view_configs.keys())

def combine_images(paths, new_name):
    images = []
    for path in paths:
        if not os.path.isfile(path):
            print(f"Unable to combine images due to missing {path}")
            return
        images.append(Image.open(path))


    # Assuming all images have the same height, adjust if not
    total_height = images[0].height

    # Calculate the width for the combined image
    total_width = sum([img.width for img in images])

    # Create a new blank image with the calculated dimensions
    combined_image = Image.new("RGB", (total_width, total_height))

    # Paste the individual images into the combined image, arranging them in columns
    x_offset = 0
    for img in images:
        combined_image.paste(img, (x_offset, 0))
        x_offset += img.width

    # Save the combined image
    combined_image.save(new_name)

def make_mega_plots(root, expected_plots):
    """
    If we have a labeling plot, attempt to make a larger image of the sequence:
        day, stalking, labeling, feeding
    This allows for a quick view at different levels
    :param root:
    :param expected_plots:
    :return:
    """
    generated_plots = glob.glob(os.path.join(data_paths["plot_root"], "*/*/*.png"))
    for plot in generated_plots:
        if 'killing' in plot:
            path0 = plot.replace('killing', 'sixhour')
            path1 = plot.replace('killing', 'stalking')
            path2 = plot
            path3 = plot.replace('killing', 'feeding')
            new_name = plot.replace('killing', 'mega')
            image_paths = [path0, path1, path2, path3]
            combine_images(image_paths, new_name)
            if os.path.isfile(new_name):
                # move mega plots up one dr
                directory_containing_file = os.path.dirname(new_name)
                parent_directory = os.path.dirname(directory_containing_file)
                new_file_path = os.path.join(parent_directory, os.path.basename(new_name))

                # Move the file
                shutil.move(new_name, new_file_path)

def get_optimal_processes():
    """
    Allow the images to generate in parallel on all but X of the cores
    """
    num_cores = multiprocessing.cpu_count()
    optimal_processes = max(1, num_cores - 4)  

    return optimal_processes

# Define a function that categorizes each row
def categorize(row, config):    
    """
    Label the behavior in the row using the start/end windows set in the ODBA spreadsheet.
    """
    try:
        # print(f"Time {row['UTC DateTime']=}")
        if config["df_stalk_start"] <= row['UTC DateTime'] < config["df_kill_start"]:
            return "STALK"
        elif config["df_kill_start"] <= row['UTC DateTime'] < config["df_kill_end"]:
            return "KILL"
        elif config["df_feed_start"] <= row['UTC DateTime'] < config["df_feed_stop"]:
            return "FEEDING"
        else:
            return "NON_KILL"
    except Exception as e:
        print(f"Error at time {row['UTC DateTime']=}")
        raise e
    
def create_csv_per_window(configs):
    raw_data_root = data_paths["raw_data_root"]
    for config in configs:
        print(f"Working on {config['Kill_ID']=}")
        # for field in config:
        #     print(f"{field=}, {config[field]}")
        input_csv = config['csv_path']
        df = pd.read_csv(input_csv, skiprows=1)
        
        # Convert 'timestamp' column from string to datetime format
        df['UTC DateTime'] = pd.to_datetime(df['UTC DateTime'])#, format='%H:%M:%S')        
        
        start_timestamp = (config["ts_kill_start"] - timedelta(hours=6)).strftime("%I:%M:%S %p")
        end_timestamp = (config["ts_kill_start"] + timedelta(hours=6)).strftime("%I:%M:%S %p")

        # TODO: this code cuts off the end of the window at midnight
        # this is because the accel csv files are of single days
        # a future improvement will be to combine the two csvs into one frame

        # Example start timestamp
        start_timestamp = config["ts_kill_start"]

        # Add six hours to the start timestamp
        end_timestamp_with_six_hours = start_timestamp + timedelta(hours=6)

        # Get the end of the current day (midnight of the next day)
        end_of_day = datetime(start_timestamp.year, start_timestamp.month, start_timestamp.day) + timedelta(days=1)

        # Compare and choose the earlier timestamp
        final_end_timestamp = min(end_timestamp_with_six_hours, end_of_day)

        # Format the timestamp
        end_timestamp = final_end_timestamp.strftime("%I:%M:%S %p")


        # Filter DataFrame based on the timestamp range
        filtered_df = df[(df['UTC DateTime'] >= start_timestamp) & (df['UTC DateTime'] <= end_timestamp)]
        
        # add the behavior label using the windows set in ODBA spreadsheet
        filtered_df['Category'] = filtered_df.apply(lambda row: categorize(row, config), axis=1)

        # Save the DataFrame to a CSV file
        # only use the lion number (remove the sex)
        output_csv = os.path.join(raw_data_root, f"acc_exp{config['Kill_ID']}_user{config['lion_id'][1:]}.txt")# '/home/matthew/AI_Capstone/ai-capstone/data/labeled_windows/F202_kill.csv'
        filtered_df.to_csv(output_csv, index=False)  # Set index=False to avoid saving row numbers as a column
        print(f"Generated RAW file: {output_csv}")

def main():
    validate_config()
    configs, expected_plots = identify_kills()
    if create_csvs:
        create_csv_per_window(configs)
        # print("STOPPING at labeled files generation for now")
        # return
    generated_scripts, expected_plots = generate_scripts(configs, expected_plots)
    
    info_scripts, info_expected_plots = get_plot_info_entries()
    generated_scripts.extend(info_scripts)
    for plot in info_expected_plots:
        expected_plots.add(plot)
    
    if launch:
        if clear_plot_dir:
            plot_root = data_paths["plot_root"]
            print(f"Clearing PNG files from plot dir: {plot_root}")
            file_pattern = os.path.join(plot_root, '*/*.png')  # remove all mega png files
            files_to_remove = glob.glob(file_pattern)
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                    # print(f"Removed file: {file_path}")
                except OSError as e:
                    print(f"Error removing file {file_path}: {e}")

        start = time.time()
        
        max_processes = get_optimal_processes()  # Adjust this based on your system's capacity
        # Using ThreadPoolExecutor to run the scripts in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_processes) as executor:
            # Submit each script to the executor
            # TODO: use generated scripts instead of updated scripts
            futures = [executor.submit(run_r_script, script) for script in generated_scripts]

            # Wait for all scripts to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Error occurred: {e}")

        runtime = time.time() - start
        print(f"Runtime: {runtime:3.0f} seconds")
        print(f"Average time per run: {runtime/len(expected_plots):2.2f} seconds")

        make_mega_plots(data_paths["plot_root"], expected_plots)

        # check expected plots
        generated_plots = glob.glob(os.path.join(data_paths["plot_root"], "*/*/*.png"))
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



if __name__ == '__main__':
    main()