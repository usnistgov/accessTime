#!/usr/bin/env python

import io
import math
import os
import pkgutil
import random
import tempfile
import unittest
from fractions import Fraction

import mcvqoe.base
import mcvqoe.simulation
import numpy as np
import scipy.io.wavfile
import scipy.signal
import xmlrunner


class AudioTest(unittest.TestCase):
    def assertTol(self, value, expected, tol):
        """Fail if value is equal within tolerance"""
        self.assertGreaterEqual(value, expected - tol * expected, f"expected value {expected}")
        self.assertLessEqual(value, expected + tol * expected, f"expected value {expected}")

    def test_basic(self):

        fs_dev = int(48e3)

        audio_file = io.BytesIO(pkgutil.get_data("mcvqoe.audio_clips", "test.wav"))
        fs_file, audio_dat = scipy.io.wavfile.read(audio_file)

        # Calculate resample factors
        rs_factor = Fraction(fs_dev / fs_file)
        # Convert to float sound array
        audio_dat = mcvqoe.base.audio_float(audio_dat)
        # Resample audio
        audio = scipy.signal.resample_poly(audio_dat, rs_factor.numerator, rs_factor.denominator)

        with mcvqoe.simulation.QoEsim(
            fs=fs_dev
        ) as sim_obj, tempfile.TemporaryDirectory() as tmp_dir:
            ap = sim_obj
            ri = sim_obj
            # generate the name for the file
            test_name = os.path.join(tmp_dir, "test.wav")
            # request access to channel
            ri.ptt(True)
            # play audio
            ap.play_record(audio, test_name)
            # release channel
            ri.ptt(False)

            self.assertTrue(os.path.exists(test_name))

    def test_m2e(self):

        fs_dev = int(48e3)

        min_corr = 0.76

        audio_file = io.BytesIO(pkgutil.get_data("mcvqoe.audio_clips", "test.wav"))
        fs_file, audio_dat = scipy.io.wavfile.read(audio_file)

        # Calculate resample factors
        rs_factor = Fraction(fs_dev / fs_file)
        # Convert to float sound array
        audio_dat = mcvqoe.base.audio_float(audio_dat)
        # Resample audio
        audio = scipy.signal.resample_poly(audio_dat, rs_factor.numerator, rs_factor.denominator)

        with mcvqoe.simulation.QoEsim(
            fs=fs_dev
        ) as sim_obj, tempfile.TemporaryDirectory() as tmp_dir:
            ap = sim_obj
            ri = sim_obj

            for m2e in (0.022, 0.1, 0.3, 0.5):
                with self.subTest(mouth2ear=m2e):
                    sim_obj.m2e_latency = m2e
                    # generate the name for the file
                    test_name = os.path.join(tmp_dir, "test.wav")
                    # request access to channel
                    ri.ptt(True)
                    # play audio
                    ap.play_record(audio, test_name)
                    # release channel
                    ri.ptt(False)

                    self.assertTrue(os.path.exists(test_name))

                    fs_file, rec_dat = scipy.io.wavfile.read(test_name)

                    pos, dly = mcvqoe.delay.ITS_delay_est(
                        audio, rec_dat, "f", fs=fs_file, min_corr=min_corr
                    )

                    # check if we got a value
                    self.assertTrue(pos)

                    estimated_m2e_latency = dly / fs_file

                    # check that we are within 1%
                    self.assertTol(estimated_m2e_latency, m2e, 0.01)

    def test_PTT_signal(self):

        fs_dev = int(48e3)

        audio_file = io.BytesIO(pkgutil.get_data("mcvqoe.audio_clips", "test.wav"))
        fs_file, audio_dat = scipy.io.wavfile.read(audio_file)

        # Calculate resample factors
        rs_factor = Fraction(fs_dev / fs_file)
        # Convert to float sound array
        audio_dat = mcvqoe.base.audio_float(audio_dat)
        # Resample audio
        audio = scipy.signal.resample_poly(audio_dat, rs_factor.numerator, rs_factor.denominator)

        with mcvqoe.simulation.QoEsim(
            fs=fs_dev
        ) as sim_obj, tempfile.TemporaryDirectory() as tmp_dir:
            ap = sim_obj
            ri = sim_obj
            # set output channels
            ap.rec_chans = {"rx_voice": 0, "PTT_signal": 1}
            ap.playback_chans = {"tx_voice": 0, "start_signal": 1}
            # generate the name for the file
            test_name = os.path.join(tmp_dir, "test.wav")

            for ptt_dly in (0.2, 0.5, 0.7, 1, 2, 2.5, 5):
                with self.subTest(dly=ptt_dly):

                    # set up radio interface to expect the start signal
                    ri.ptt_delay(ptt_dly, use_signal=True)
                    # play/record audio
                    ap.play_record(audio, test_name)

                    state = ri.waitState()

                    ri.ptt(False)

                    self.assertEqual(state, "Idle")

                    fs_file, audio_dat = scipy.io.wavfile.read(test_name)

                    # Calculate niquest frequency
                    fn = fs_file / 2

                    # Create lowpass filter for PTT signal processing
                    ptt_filt = scipy.signal.firwin(400, 200 / fn, pass_zero="lowpass")

                    # Extract push to talk signal (getting envelope)
                    ptt_sig = scipy.signal.filtfilt(ptt_filt, 1, abs(audio_dat[:, 1]))

                    # Get max value
                    ptt_max = np.amax(ptt_sig)

                    # Normalize levels
                    ptt_sig = (ptt_sig * math.sqrt(2)) / ptt_max

                    # check levels
                    self.assertFalse(ptt_max < 0.25)

                    # get PTT start index
                    ptt_st_idx = np.nonzero(ptt_sig > 0.5)[0][0]

                    # Convert sample index to time
                    st = ptt_st_idx / fs_file

                    # check if we are within 1%
                    self.assertTol(st, ptt_dly, 0.01)


class ProbabilityiserTest(unittest.TestCase):
    def test_update_state(self):
        expected_states = [
            [1, 1, 1, 3, 3, 2, 3, 2, 3, 3, 2],
            [1, 3, 2, 2, 3, 3, 3, 2, 2, 3, 3],
            [1, 1, 1, 3, 3, 2, 2, 2, 3, 2, 2],
            [1, 3, 2, 3, 2, 2, 3, 3, 2, 3, 3],
            [1, 3, 3, 3, 3, 3, 3, 2, 2, 2, 3],
            [1, 1, 1, 1, 1, 1, 1, 3, 3, 2, 2],
            [1, 1, 1, 3, 3, 3, 2, 3, 2, 3, 2],
            [1, 3, 3, 2, 3, 2, 3, 3, 2, 3, 3],
            [1, 3, 2, 3, 2, 3, 3, 2, 3, 2, 3],
            [1, 3, 3, 3, 2, 3, 2, 2, 3, 2, 2],
        ]

        for i, expected_seq in enumerate(expected_states):
            pbi = mcvqoe.simulation.PBI(P_a1=0.5, P_r=0.5)
            random.seed(i)
            states = []
            states.append(pbi.state)
            for j in range(10):
                pbi.update_state()
                states.append(pbi.state)

            self.assertEqual(states, expected_seq, msg=f"Seed: {i}")

    def test_process_audio(self):
        input_data = np.ones([10], dtype=int)

        expected_audio = [
            [0, 1, 0, 1, 0, 0, 0, 1, 0, 1],
            [1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
            [1, 0, 0, 1, 1, 1, 1, 0, 0, 0],
            [1, 0, 0, 0, 1, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 1, 1, 0, 0, 1, 0],
            [0, 1, 0, 1, 0, 1, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 0, 1, 0, 1, 1],
            [0, 0, 0, 1, 0, 0, 0, 1, 1, 1],
            [1, 0, 1, 1, 1, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 1, 0, 1, 1, 1, 1],
        ]
        for i, exp_dat in enumerate(expected_audio):
            pbi = mcvqoe.simulation.PBI(P_a1=0.5, P_r=0.5)
            random.seed(i + 10)
            exp_dat = np.asarray(exp_dat)
            res = pbi.process_audio(input_data, 1)
            self.assertTrue(
                (res == exp_dat).all(),
                msg=f"Seed: {i + 10}, Expected Result: {exp_dat}, Received: {res}",
            )


if __name__ == "__main__":
    with open("sim-tests.xml", "wb") as outf:
        unittest.main(
            testRunner=xmlrunner.XMLTestRunner(output=outf),
            failfast=False,
            buffer=False,
            catchbreak=False,
        )
