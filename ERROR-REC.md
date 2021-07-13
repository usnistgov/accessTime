# Access Time Error Recovery

The 'RetryFunc' parameter in test.m is used for error recovery. When the A-weight power of P2 is below 'SThresh' after 'STries' retries in a row, the 'RetryFunc' is called. The 'RetryFunc' is passed three arguments: `calls`, `trialCount` and `clip_count`. The `calls` parameter gives the number of times the 'RetryFunc' has been called for this trial. The `trialCount` is the number of trials that have been run in the test. The `clip_count` parameter is the number of trials that have been run for the current audio clip. The 'RetryFunc' returns 0 if the test should try again to run audio through the communications system and return 1 if the test should be stopped for human intervention.

An example 'RetryFunc' is included, `example_restart.m`. This Matlab function calls python code from the `example_adb.py` which is also an example function that will need to be adapted to your application. The python function calls the ADB utility which talks to the android devices. The python code looks for adb both in the windows install location under `LOCALAPPDATA` and in the path. If it is not in one of these locations then `example_adb.py` will have to be modified. The Android name of the application and phone unlock pin must also be modified in the code based on your setup.