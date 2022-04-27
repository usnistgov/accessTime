# Measurement Data Structure

All MCV QoE measurements save data with the following directory structure.
Coarsely the directory structure is as follows:

## Directory structure
* data
  * csv (required)
  * wav (required)
  * 2loc_rx-data (optional)
  * 2loc_tx-data (optional)
  * recovery (optional)
  * error (optional)
* data_matfiles (for users of the legacy system)


### data folder
Contains all data from tests.

#### csv (required)
Contains csv files for each test with all output measurement data. All measurement files are of the form `capture_{Description}_DD-Mon-YYYY_HH-MM-SS.csv` or `capture_{Description}_DD-Mon-YYYY_HH-MM-SS_{Audio File}.csv`.

Data that has been reprocessed follows the same format but has a `R` prefix as well, such as 
`Rcapture_{Description}_DD-Mon-YYYY_HH-MM-SS_{Audio File}.csv`.


#### wav (required)
Contains folders for each test containing all transmit and receive audio.
Folders are of the form `capture_{Description}_DD-Mon-YYYY_HH-MM-SS`.

Transmit audio clips should be named in the following convention: `Tx_{clip-name}.wav` and should always have the associated cutpoints file in the same directory if applicable named `Tx_{clip-name}.csv`.

Received audio clips can be stored in the wav folder or within a zipped file called `audio.zip`. Each received audio file should be named in the following convention: `Rx{trial-number}_{clip-name}.wav`.

For trials that were deemed a failure, audio clips are named as `BAD{trial-number}_r{retry-number}_{clip-name}.wav`.

#### 2loc_rx-data (optional)
Contains data from the receive side of two location tests. There should be a single .wav file and .json file for each test.

#### 2loc_tx-data (optional)

Contains data from the transmit side of two location tests. There should be one subfolder, labeled as `Tx_capture_2loc-{Description}_DD-Mon-YYYY_HH-MM-SS` for each test that contains the Tx audio and timecode recordings in a similar format to the wav directory. 

#### recovery (optional)

Contains files used to restart a test that has stopped. Format is dependent on test. This folder is not synced.

#### error (optional)

Contains information about why a test may have stopped. Information can be stored here that does not fit into a log entry but could aid in debugging.

### data_matfiles (legacy)
Contains old data files from old test code if users ran tests with the legacy system. Do not use this in new code! 
