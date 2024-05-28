# ai-capstone
AI Capstone Project - Linking Fine-Scale Behaviors to Spatial Interactions Between Apex Predators
TODO: Link to final report (currently WIP)

# Environment
To run most scripts (everything but model)
> conda activate ai_capstone

To run BEBE model
> conda activate BEBE_GPU

# Testing
To run all tests, run the 'run_all_tests.py' script. This will report a status for every test in the tests subdir. If you would like more info about an individual test, run that particular test file directly.

Source the BEBE_GPU env and execute run_all_tests.py from the root dir, e.g.:
> conda activate BEBE_GPU ;
> python tests/run_all_tests.py

# General scripts
This section contains a high level overview of the scripts in the repo. For more details, refer to the specific files.
## one_off_data_processing
Created for single task, kept around in case similar operation needed.
