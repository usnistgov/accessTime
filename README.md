# mcvqoe Python Package

Common code for MCV QoE Measurement Methods. This package contains core code for 
QoE measurements used in the following packages:

* <https://github.com/usnistgov/mcvqoe>
* <https://github.com/usnistgov/mouth2ear>
* <https://github.com/usnistgov/accessTime>
* <https://github.com/usnistgov/psud>
* <https://github.com/usnistgov/intelligibility>
* <https://github.com/usnistgov/MCV-QOE-TVO>

The `mcvqoe-base` package includes libraries to play audio through a Push To 
Talk (PTT) communication system. Also included are equivalent libraries to 
simulate sending audio through a PTT communication system.

# Building and Instally the Package Locally

To build and install the package
```
python setup.py install
```

# Radio Interface Firmware

The firmware for the RadioInterface board can be found at:

<https://github.com/usnistgov/MCV-QoE-firmware>

# Measurement Data Structure

For more information about how measurement data gets stored see <DataStructure.md>

# License

This software was developed by employees of the National Institute of Standards 
and Technology (NIST), an agency of the Federal Government. Pursuant to title 17 
United States Code Section 105, works of NIST employees are not subject to 
copyright protection in the United States and are considered to be in the public 
domain. Permission to freely use, copy, modify, and distribute this software and 
its documentation without fee is hereby granted, provided that this notice and 
disclaimer of warranty appears in all copies.

THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER 
EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY 
THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND FREEDOM FROM INFRINGEMENT, 
AND ANY WARRANTY THAT THE DOCUMENTATION WILL CONFORM TO THE SOFTWARE, OR ANY 
WARRANTY THAT THE SOFTWARE WILL BE ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE 
FOR ANY DAMAGES, INCLUDING, BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR 
CONSEQUENTIAL DAMAGES, ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED 
WITH THIS SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR 
OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR 
OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE 
RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
