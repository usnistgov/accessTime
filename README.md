# mcvqoe Python Package
Common code for MCV QoE Measurement Methods

# Building and Instally the Package Locally

To build the package
```
#remove old packages and stuff
rm -r dist
rm -r build

#pull the latest version
git pull

#run setup script
python setup.py sdist bdist_wheel
```
To install the package

```
#remove old package
python -m pip uninstall mcvqoe-nist

#install new package
python -m pip install --find-links ./dist/ mcvqoe-nist

```

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

# Radio Interface Firmware
In order to update the firmware currently you must:
* Download Code Composer Studio (CCS)
* Clone from gitlab 
* Compile
* Download to RI board

Future plans: 
* Write python code to update firmware automagically.
* Add a check to radio interface class that complains if your FW is out of date.

# License

This software was developed by employees of the National Institute of Standards and Technology (NIST), an agency of the Federal Government. Pursuant to title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States and are considered to be in the public domain. Permission to freely use, copy, modify, and distribute this software and its documentation without fee is hereby granted, provided that this notice and disclaimer of warranty appears in all copies.

THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
