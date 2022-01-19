# PURPOSE

The purpose of this software is to measure the access delay of a push-to-talk (PTT) network.
Access time generally describes time associated with the initialization and assignment
of channels upon user request to speak and has been identified as a key component of
quality of experience (QoE) in communications. NIST’s PSCR division developed a method
to measure and quantify the access time of any PTT communication system.

# OBTAINING SOFTWARE

- Access Time measurement software available at:  https://github.com/usnistgov/accessTime
- Microcontroller firmware available at:  https://github.com/usnistgov/MCV-QoE-firmware
- MCV QoE GUI software available at : https://github.com/usnistgov/mcvqoe
- Core MCV QoE library available at : https://github.com/usnistgov/mcvqoe-base

# OBTAINING PAPERS

- Start-of-word correction paper available at: https://doi.org/10.6028/NIST.TN.2166
- Addendum Paper available at: https://doi.org/10.6028/NIST.IR.8328
- Orignal measurement system paper available at: https://doi.org/10.6028/NIST.IR.8275

# OBTAINING DATA
- Start-of-word correction data available at: https://doi.org/10.18434/mds2-2411
- Addendum measurement data available at: https://doi.org/10.18434/mds2-2356
- Original measurement system data available at:  https://doi.org/10.18434/M32083

# HARDWARE REQUIREMENTS

- 1 computer able to run Python 3.9 or newer
- 1 audio interface
- 2 push-to-talk communications devices for testing
- QoE hardware
- cables to connect test devices to QoE hardware
- Audio cables to connect QoE hardware to audio interface

# RUNNING MEASUREMENT SOFTWARE

The easiest way to use the measurement system is to run the GUI (https://github.com/usnistgov/mcvqoe).

# Post Processing

# Calculating Access Time and Uncertainty

If access time is run through the GUI, the user will be guided through the 
process of calculating access time. Using the GUI is the recomended way, but it
can also be done by running the following python code:

```
eval_obj = mcvqoe.accesstime.evaluate(filepaths)
mean, ci = eval_obj.eval(alpha=0.9)
```

Where `filepaths` is a list that contains the path to the .csv files from the 
test to evaluate.

# Microcontroller Code
The code, as well as additional instructions, for the radio interface microcontroller is located:  <https://doi.org/10.18434/M32086>. 

This code was designed to run on the MSP-EXP430F5529LP "Launch Pad" development board and compiled for the MSP430 using TI Code Composer Studio. The microcontroller code sets up a virtual COM port over USB and provides a simple command line interface. This code is compatible with the modifications attached via perfboard.

The code uses the standard TI USB library and serial drivers. On Windows 10 driver installation is not necessary. On other systems the appropriate driver may need to be downloaded from TI.

# TECHNICAL SUPPORT
For more information or assistance on access delay measurements please contact:

Public Safety Communications Research Division\
National Institute of Standards and Technology\
325 Broadway\
Boulder, CO 80305\
PSCR@PSCR.gov

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
