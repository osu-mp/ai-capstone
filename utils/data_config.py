import os.path
from pathlib import Path
import platform

# get the project root as the parent of the parent directory of this file
ROOT_DIR = Path(__file__).parent.parent.absolute()

is_unix = 'Linux' in platform.system()

csv_root = "C:/accel_data/cougars"
if is_unix:
    csv_root = "/home/matthew/AI_Capstone/accel_data/cougars"


experiment_name = "cougar_F202_1hr_1hz"

"""
Various disk paths for where to read and write data
"""
data_paths = {
    "spreadsheet_root": f"{ROOT_DIR}/data",
    "csv_backup": f"{ROOT_DIR}/data/csv_backup",
    "template_path": f"{ROOT_DIR}/rcode/template.r",
    "output_path": f"{ROOT_DIR}/rcode/jobs/",
    "r_path": "C:\\Program Files\\R\\R-4.3.1\\bin\\Rscript.exe",
    "plot_root": f"{ROOT_DIR}/plots/",
    "raw_data_root": f"{ROOT_DIR}/BEBE-datasets/raw_{experiment_name}/RawData/",   # dir where spreadsheet script writes files for BEBE formatter
    "formatted_data_root": f"{ROOT_DIR}/BEBE-datasets/format_{experiment_name}/",   # dir where BEBE formatted datasets live
}

if is_unix:
    data_paths['r_path'] = "/usr/bin/Rscript"
    # data_paths['plot_root'] = "/home/matthew/AI_Capstone/plots"

"""
Spreadsheets to pull target times from
Each root key represents a spreadsheet file (relative to spreadsheet_root)
    Each 'tabs' key per spreadsheets controls which tabs of the spreadsheet are read
    If there is no 'tabs' entry, all tabs will be read.
"""
spreadsheets = {
    "Cougars_ODBA_KIlls_Setup.xlsx": {
        "tabs": {
            "M201": f"{csv_root}/M201_20170_020116_120116/MotionData_0/",
            "F202": f"{csv_root}/F202_27905_010518_072219/MotionData_27905",
            "F207": f"{csv_root}/F207_22263_030117_012919/MotionData_0",
            "F209": f"{csv_root}/F209_22262_030717_032819/MotionData_22262/",
        },
        "data_cols": ["AnimalID", "Sex", "Period", "Kill_ID", "Start Date", "Start time", "End Time", "StartStalk", "StartKill", "EndCons", "EndLib", "FeedStart", "FeedStop"],

        "data_cols_info": ["AnimalID", "Sex", "Kill_ID", "Start Date", "Start time", "End time", 
                           "MarkerTime1", "MarkerLabel1", "MarkerTime2",  "MarkerLabel2","PlotLabel"]
    }
}

constants = {
    "INPUT_SAMPLE_RATE": 16,      # input from cougar collars is 16Hz
    "OUTPUT_SAMPLE_RATE": 1,     # desired output (Hz) to feed into BEBE models (unused yet)
}


"""
Configs for different data windows we may care about.
Must specify the number of minutes before and after the event
of interest we want.
"""
view_configs = {
    # labeling: narrow window around original timestamp to refine window
    "killing": {
        "window_pre_mins": 1,
        "window_post_mins": 1,
        "minor_tick_interval": 5,
    },
    # stalking: short before, short after
    "stalking": {
        "window_pre_mins": 10,
        "window_post_mins": 2,
        "minor_tick_interval": 30,
    },
    # feeding: short before, long after
    "feeding": {
        "window_pre_mins": 2,
        "window_post_mins": 30,
        "minor_tick_interval": 60,
    },
    
    # day: several hours before and after (will not cross days yet)
    "day": {
        "window_pre_mins": 24*60,
        "window_post_mins": 24*60,
        "minor_tick_interval": 60 * 60,     # every hour
    },
    # sixhour: shorter than day window, still wide window
    "sixhour": {
        "window_pre_mins": 6 * 60,
        "window_post_mins": 6 * 60,
        "minor_tick_interval": 60 * 60,     # every hour
    }
}

plot_lines = {
    "default": [
        {"label": "Original", "value": "window_high, window_low", "color": "orange", "alpha": "0.3", "linetype": "solid"},
        {"label": "KillStart", "value": "cons_window_low", "color": "darkred", "alpha": "0.8", "linetype": "solid"},
        {"label": "KillEndPhase1", "value": "cons_window_high", "color": "green", "alpha": "0.9", "linetype": "dashed"},
        {"label": "KillEndPhase2", "value": "lib_window_high", "color": "darkblue", "alpha": "0.9", "linetype": "dashed"},
        {"label": "StalkStart", "value": "stalk_window_start", "color": "yellow", "alpha": "0.75", "linetype": "solid"},
        {"label": "FeedStart", "value": "feed_window_start", "color": "magenta", "alpha": "0.75", "linetype": "solid"},
        {"label": "FeedStop", "value": "feed_window_stop", "color": "purple", "alpha": "0.75", "linetype": "solid"},
    ],
    "info_plot": [
        {"label": "{marker_1_label}", "value": "marker_1", "color": "green", "alpha": "0.75", "linetype": "solid"},
        {"label": "{marker_2_label}", "value": "marker_2", "color": "orange", "alpha": "0.75", "linetype": "solid"},
    ],
    "sixhour": [],

}

def validate_config():
    """
    Sanity check of values in the config:
    -are relevant keys present
    -can dirs/data be found
    :return:
    """
    print("Checking config")
    spreadsheet_root = data_paths["spreadsheet_root"]
    assert(os.path.isdir(spreadsheet_root)), f"Unable to find input data dir: {spreadsheet_root}"
    assert(os.access(data_paths["template_path"], os.R_OK)), f"Unable tp read template file: {data_paths['template_path']}"
    os.makedirs(data_paths["output_path"], exist_ok=True)
    assert(os.access(data_paths["output_path"], os.W_OK)), f"Unable to write to output dir: {data_paths['output_path']}"
    assert(os.access(data_paths["r_path"], os.X_OK)), "Unable to find/execute R"

    os.makedirs(data_paths["plot_root"], exist_ok=True) # "Unable to make plot root dir"
    assert(os.access(data_paths["plot_root"], os.W_OK)), "Unable to write to plot dir"

    os.makedirs(data_paths["raw_data_root"], exist_ok=True)
    assert(os.access(data_paths["raw_data_root"], os.W_OK)), "Unable to write to raw_data dir"

    for spreadsheet in spreadsheets:
        fname = os.path.join(spreadsheet_root, spreadsheet)
        assert(os.access(fname, os.R_OK)), f"Unable to read spreadsheet: {fname}"

    for key, value in view_configs.items():
        assert("window_pre_mins" in value), f"Missing window_pre_mins for view_configs[{key}]"
        assert ("window_post_mins" in value), f"Missing window_post_mins for view_configs[{key}]"
        assert ("minor_tick_interval" in value), f"Missing minor_tick_interval for view_configs[{key}]"

    # sanity checks for sampling rates
    assert constants['INPUT_SAMPLE_RATE'] == 16, "Input sample rate should always be 16"
    assert 0 < constants['OUTPUT_SAMPLE_RATE'] <= constants['INPUT_SAMPLE_RATE'], f"Output sample rate must be positive and less than input sample rate ({constants['INPUT_SAMPLE_RATE']} Hz)"
    assert constants['INPUT_SAMPLE_RATE'] % constants['OUTPUT_SAMPLE_RATE'] == 0, f"Input sample rate must divide evenly into into output"

    print("Data config checks passed\n")

    return view_configs

if __name__ == '__main__':
    validate_config()
