# Measurement Data Structure

All MCV QoE measurements save data with the following directory structure.

Coarsely the directory structure is as follows

## Data Filenames
All captured data should adhere to the following naming conventions:

`capture_{Description}_DD-Mon-YYYY_HH-MM-SS_{Audio File}.csv`

Data that has been reprocessed has an `R` prefix as well

`Rcapture_{Description}_DD-Mon-YYYY_HH-MM-SS_{Audio File}.csv`

## Directory structure

* data
  * csv (required)
  * wav (required)
  * 2loc_rx-data (optional)
  * 2loc_tx-data (optional)
  * recovery (optional)
  * error (optional)
* data_matfiles


### data folder
Contains all data from tests.

#### csv (required)
Contains csv files for each test with all output measurement data. All measurement files are of the form `capture_{Description}_DD-Mon-YYYY_HH-MM-SS_{Audio File}.csv`

Data that has been reprocessed follows the same format but has a `R` prefix as well.

#### wav (required)
Contains folders for each test containing all transmit and receive audio. 

Transmit audio clips should be named in the following convention: `Tx_{clip-name}.wav` and should always have the associated cutpoints file in the same directory if applicable named `Tx_{clip-name}.csv`.

Received audio clips can be stored in the wav folder or within a zipped file called `audio.zip`. Each received audio file should be named in the following convention: `Rx{trial-number}_{clip-name}.wav`.

For trials that were deemed a failure, audio clips are named as `BAD{trial-number}_r{retry-number}_{clip-name}.wav`.

#### 2loc_rx-data (optional)
Contains data from the receive side of two location tests. This should be a single .wav file for each test.

#### 2loc_tx-data (optional)

Contains data from the transmit side of two location tests. There should be one subfolder for each test that contains the Tx audio and timecode recordings in a siilar format to the wav directory. 

#### recovery (optional)

Contains files used to restart a test that has stopped. Format is dependant on test. This folder is not synced.

#### error (optional)

Contains information about why a test may have stopped. Information can be stored here that does not fit into a log entry but could aid in debugging.

### data_matfiles (legacy)
Contains old data files from old test code. Do not use this in new code, not synced! 

## Date format
Put something here about dates in filenames...
