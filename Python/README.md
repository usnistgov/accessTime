# PURPOSE

The purpose of this software is to measure the access delay of a push-to-talk network.
Access time generally describes time associated with the initialization and assignment
of channels upon user request to speak and has been identified as a key component of
quality of experience (QoE) in communications. NIST’s PSCR division developed a method
to measure and quantify the access time of any push to talk (PTT) communication system.

# OBTAINING SOFTWARE, DATA, AND PAPER
- Code available at:  https://gitlab.nist.gov/gitlab/PSCR/MCV/access-release
- Code available at:  https://github.com/usnistgov/MCV-QoE-firmware
- Data available at:  https://doi.org/10.18434/M32083
- Paper available at: https://doi.org/10.6028/NIST.IR.8275
- Addendum Paper available at: https://doi.org/10.6028/NIST.IR.8328

# HARDWARE REQUIREMENTS
- 1 computer able to run Python and R
- 1 audio interface
- 2 communications devices for testing
- cables to connect test devices to audio interfaces
- 1 microcontroller with daughter board
- transformers

**Additional details, reference the paper linked above.**

# SOFTWARE REQUIREMENTS
- Python 3.8.6 or newer
- mcv-qoe-library: https://gitlab.nist.gov/gitlab/PSCR/MCV/mcv-qoe-library
- R version 3.5.X or newer
    - RStudio (recommended)
	- ggplot2, minpack.lm packages (will install on accessTime package install)
    - devtool package (must be installed via `install.packages("devtools")` )

**Additional requirement information can be found in the paper.**	

# RUNNING MEASUREMENT SOFTWARE
To run the access delay test, run `python access_time.py -k <access-time-audio-path> -a <audio_file>` in a terminal opened to the top level directory. Speech will be played and recorded using the connected audio device. The raw and processed audio data is stored in a subfolder named data/. access_time.py takes in a variety of optional input parameters, descriptions of these are available by typing `python access_time.py -h` in a teriminal opened to the top level directory. 

Example input specifications:
`python access_time.py -k D:/access-time-audio/T_2500ms-varyFilled -a F1_b9_w1_bed.wav -y 2.0 2.56 -t Inf -p .03 -s 0.0 -c True -f 9 -e 16`
* `-k D:/access-time-audio/T_2500ms-varyFilled` uses this file path to search for given audio file
* `-a F1_b9_w1_bed.wav` adds this audio file to be tested (must have matching .csv file in folder)
* `-y 2.0 2.56` places 2.0 and 2.56 into a double vector for push to talk delay. 2.0 being the smallest delay used, and 2.56 the largest
* `-t Inf` is the number of trials to use for a test, and in this case it's set to infinite
* `-p .03` sets the time in between successive ptt delays to 30ms
* `-s 0.0` sets the time to pause after completing one trial and starting the next to 0.0s
* `-c True` turns on the auto_stop capabilities. This checks for access and stops the test when it has been detected a set number of times
* `-f 9` sets the number of times that access must be detected in a row before the test is completed
* `-e 16` sets the number of times to repeat a given ptt delay

# Post Processing

# Calculating Access Time and Uncertainty
The code to calculate access time values and their associated uncertainties is in the folder accessTime, as an R package. The package can be installed via the following command in the R console: `devtools::install_git(url="git://github.com/usnistgov/accessTime", subdir = "accessTime")`.

Detailed documentation, with examples, is built into the R package. An index containing all documentation files as well as the description file can be found via the following command in the R console, after the package has been installed: `help(package="accessTime")`

The wrapper function `process_accessData(sessionFiles, cutDir)` reads in access delay data from a list of csv files given by `sessionFiles` for measurements using audio files contained in the path of `cutDir`, along with the cut points files. It reads in the data, treats it, and fits a logistic function to the treated data. It returns an accessFit object.

The functions `eval_intell(accFit, t)` and `eval_access(accFit,alpha)` evaluate accessFit objects at times and fractions of asymptotic intelligibilities respectfully. They return intelligibilities as a function of time or access delays as a function of achieved fractional asymptotic intelligibility.

A series of plotting functions are included to visualize the results from `eval_intell(...)` and `eval_access(...)`. These functions are: `plot_accessCurve(...)`, `plot_compareAccessCurves(...)`,`plot_techIntCurves(...)`,`plot_wordIntCurves(...)`. Each have their own documentation and examples.

# Microcontroller Code
The code, as well as additional instructions, for the radio interface microcontroller is located:  <https://doi.org/10.18434/M32086>. 

This code was designed to run on the MSP-EXP430F5529LP "Launch Pad" development board and compiled for the MSP430 using TI Code Composer Studio. The microcontroller code sets up a virtual COM port over USB and provides a simple command line interface. This code is compatible with the modifications attached via perfboard.

The code uses the standard TI USB library and serial drivers. On Windows 10 driver installation is not necessary. On other systems the appropriate driver may need to be downloaded from TI.

# DISCLAIMER
**Much of the included software was developed by NIST employees, for that software the following disclaimer applies:**

This software was developed by employees of the National Institute of Standards and Technology (NIST), an agency of the Federal Government. Pursuant to title 17 United States Code Section 105, works of NIST employees are not subject to copyright protection in the United States and are considered to be in the public domain. Permission to freely use, copy, modify, and distribute this software and its documentation without fee is hereby granted, provided that this notice and disclaimer of warranty appears in all copies.

THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.

**Some software included was developed by NTIA employees, for that software the following disclaimer applies:**

THE NATIONAL TELECOMMUNICATIONS AND INFORMATION ADMINISTRATION,
INSTITUTE FOR TELECOMMUNICATION SCIENCES ("NTIA/ITS") DOES NOT MAKE
ANY WARRANTY OF ANY KIND, EXPRESS, IMPLIED OR STATUTORY, INCLUDING,
WITHOUT LIMITATION, THE IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR
A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY.  THIS SOFTWARE
IS PROVIDED "AS IS."  NTIA/ITS does not warrant or make any
representations regarding the use of the software or the results thereof,
including but not limited to the correctness, accuracy, reliability or
usefulness of the software or the results.

You can use, copy, modify, and redistribute the NTIA/ITS developed
software upon your acceptance of these terms and conditions and upon
your express agreement to provide appropriate acknowledgments of
NTIA's ownership of and development of the software by keeping this
exact text present in any copied or derivative works.

The user of this Software ("Collaborator") agrees to hold the U.S.
Government harmless and indemnifies the U.S. Government for all
liabilities, demands, damages, expenses, and losses arising out of
the use by the Collaborator, or any party acting on its behalf, of
NTIA/ITS' Software, or out of any use, sale, or other disposition by
the Collaborator, or others acting on its behalf, of products made
by the use of NTIA/ITS' Software.


**Audio files included with this software were derived from the MRT Audio Library.**