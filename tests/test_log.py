#!/usr/bin/env python


import datetime
import os.path
import tempfile
import unittest

import mcvqoe.base
import mcvqoe.simulation
import mcvqoe.utilities


# fake test class for logging purposes
class FakeTest:
    no_log = ()

    def __init__(self):
        sim_obj = mcvqoe.simulation.QoEsim()
        self.ri = sim_obj
        self.audioInterface = sim_obj


class LogTest(unittest.TestCase):
    def test_write_read_error(self):
        # make a fake test class
        dummy = FakeTest()

        info = mcvqoe.base.write_log.fill_log(dummy)

        self.assertEqual(info["RI version"], mcvqoe.base.version)
        self.assertEqual(info["RI id"], "QoEsim.py")
        self.assertEqual(info["filename"], os.path.basename(__file__))
        self.assertEqual(info["mcvqoe version"], mcvqoe.base.version)
        self.assertEqual(
            info["Arguments"], f"ri = {str(dummy.ri)},audioInterface = {str(dummy.audioInterface)}"
        )

        info["test"] = "unittest"
        # give our test a date
        info["Tstart"] = datetime.datetime(1953, 3, 24)
        info["Pre Test Notes"] = "Starting test, hopefully nothing goes too wrong\n"

        # make a temp dir to store logs in
        with tempfile.TemporaryDirectory() as tmp_dir:

            mcvqoe.base.write_log.pre(info, outdir=tmp_dir)
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "tests.log")))
            pre_size = os.stat((os.path.join(tmp_dir, "tests.log"))).st_size

            # add post notes
            info["Error Notes"] = "Things went horribly wrong\n"

            mcvqoe.base.write_log.post(info, outdir=tmp_dir)
            self.assertGreater(os.stat(os.path.join(tmp_dir, "tests.log")).st_size, pre_size)

            ls = mcvqoe.utilities.log_search(
                os.path.join(tmp_dir, "tests.log"), LogParseAction="Error"
            )

            info["operation"] = info.pop("test")
            info["pre_notes"] = info.pop("Pre Test Notes")
            info["error_notes"] = info.pop("Error Notes")
            info.pop("Tstart")
            for k, v in info.items():
                self.assertIn(k, ls.log[0], msg=k)
                self.assertEqual(ls.log[0][k].strip(), info[k].strip(), msg=k)
            # [print(k) for k in ls.log[0].keys() if k not in info]
            self.assertEqual(ls.Qsearch("operation", "unittest"), {0})
            self.assertEqual(
                ls.MfSearch({"operation": "unittest", "complete": True, "error": True}), {0}
            )

    def test_write_read_normal(self):
        # make a fake test class
        dummy = FakeTest()

        info = mcvqoe.base.write_log.fill_log(dummy)

        self.assertEqual(info["RI version"], mcvqoe.base.version)
        self.assertEqual(info["RI id"], "QoEsim.py")
        self.assertEqual(info["filename"], os.path.basename(__file__))
        self.assertEqual(info["mcvqoe version"], mcvqoe.base.version)
        self.assertEqual(
            info["Arguments"], f"ri = {str(dummy.ri)},audioInterface = {str(dummy.audioInterface)}"
        )

        info["test"] = "unittest"
        # give our test a date
        info["Tstart"] = datetime.datetime(1953, 8, 21)
        info["Pre Test Notes"] = "Perhaps this works now\n"

        # make a temp dir to store logs in
        with tempfile.TemporaryDirectory() as tmp_dir:

            mcvqoe.base.write_log.pre(info, outdir=tmp_dir)
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "tests.log")))
            pre_size = os.stat((os.path.join(tmp_dir, "tests.log"))).st_size

            info["Post Test Notes"] = "Everything is as it should be\n"
            mcvqoe.base.write_log.post(info, outdir=tmp_dir)
            self.assertGreater(os.stat(os.path.join(tmp_dir, "tests.log")).st_size, pre_size)

            ls = mcvqoe.utilities.log_search(
                os.path.join(tmp_dir, "tests.log"), LogParseAction="Error"
            )

            info["operation"] = info.pop("test")
            info["pre_notes"] = info.pop("Pre Test Notes")
            info["post_notes"] = info.pop("Post Test Notes")
            info.pop("Tstart")
            for k, v in info.items():
                self.assertIn(k, ls.log[0], msg=k)
                self.assertEqual(ls.log[0][k].strip(), info[k].strip(), msg=k)
            # [print(k) for k in ls.log[0].keys() if k not in info]
            self.assertEqual(ls.Qsearch("operation", "unittest"), {0})
            self.assertEqual(
                ls.MfSearch({"operation": "unittest", "complete": True, "error": True}), set()
            )


if __name__ == "__main__":
    print(__file__)
    unittest.main()
