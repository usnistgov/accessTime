#!/usr/bin/env python

import unittest
import tempfile
import os
import mcvqoe.utilities.test_copy as testCpy

# get the location of test files
test_dat = os.path.join(os.path.dirname(__file__), "testCpy_files")


class TestCpyTest(unittest.TestCase):
    def test_log_update(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_in1 = os.path.join(test_dat, "in1.log")
            log_out = os.path.join(tmp_dir, "tests.log")
            # call log update, this will create the output log
            testCpy.log_update(log_in1, log_out)
            # file should exist now
            self.assertTrue(os.path.exists(log_out))
            # use an updated input log
            log_in2 = os.path.join(test_dat, "in2.log")
            # run again, this should update the log
            testCpy.log_update(log_in2, log_out)


if __name__ == "__main__":
    unittest.main()
