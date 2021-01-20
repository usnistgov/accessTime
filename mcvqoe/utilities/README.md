# Utilities
This folder provides code to assist with managing data between test machines, network storage, and local machines.

## Example flow
* testCpy from test machine
  * Calls sync from HD (copies if not there already)
* testCpy from HD while plugged into something with connection to network storage
* local-copy
* log-search

## testCpy
testCpy is designed to simplify transferring test data from a test machine to an external hard-drive (HD). It stores the serial number of an HD so it can be found, and updates log files stored on the HD. It sets up a HD to have to be able to run sync and uses that copy files. testCpy will also put a version file of the mcvqoe package on the HD so it knows when it's out of date.

## sync
Copy files. Designed to run from HD with arguments in order to copy files from test machine to HD. testCpy handles this case, and calls sync with the proper arguments.

When run with no arguments copies to network.


## local-copy


## log-search

