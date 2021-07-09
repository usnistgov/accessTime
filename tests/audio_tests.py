#!/usr/bin/env python

import mcvqoe.hardware
import unittest
import tempfile
import pkgutil
import scipy.io.wavfile
import scipy.signal
from fractions import Fraction
import io
import os

# NOTE : these tests require that a RadioInterface and audio interface are plugged
#       in to the machine running the test!


class AudioTest(unittest.TestCase):
    def test_basic(self):

        fs_dev = int(48e3)

        audio_file = io.BytesIO(
            pkgutil.get_data("mcvqoe.hardware", "audio_clips/test.wav")
        )
        fs_file, audio_dat = scipy.io.wavfile.read(audio_file)

        # Calculate resample factors
        rs_factor = Fraction(fs_dev / fs_file)
        # Convert to float sound array
        audio_dat = mcvqoe.audio_float(audio_dat)
        # Resample audio
        audio = scipy.signal.resample_poly(
            audio_dat, rs_factor.numerator, rs_factor.denominator
        )

        ap = mcvqoe.hardware.AudioPlayer(fs=fs_dev)

        with mcvqoe.hardware.RadioInterface() as ri, tempfile.TemporaryDirectory() as tmp_dir:
            # generate the name for the file
            test_name = os.path.join(tmp_dir, "test.wav")
            # request access to channel
            ri.ptt(True)
            # play audio
            ap.play_record(audio, test_name)
            # release channel
            ri.ptt(False)

            self.assertTrue(os.path.exists(test_name))

    def test_start_signal(self):

        fs_dev = int(48e3)

        audio_file = io.BytesIO(
            pkgutil.get_data("mcvqoe.hardware", "audio_clips/test.wav")
        )
        fs_file, audio_dat = scipy.io.wavfile.read(audio_file)

        # Calculate resample factors
        rs_factor = Fraction(fs_dev / fs_file)
        # Convert to float sound array
        audio_dat = mcvqoe.audio_float(audio_dat)
        # Resample audio
        audio = scipy.signal.resample_poly(
            audio_dat, rs_factor.numerator, rs_factor.denominator
        )

        ap = mcvqoe.hardware.AudioPlayer(
            fs=fs_dev,
            rec_chans={"rx_voice": 0, "PTT_signal": 1},
            playback_chans={"tx_voice": 0, "start_signal": 1},
        )

        with mcvqoe.hardware.RadioInterface() as ri, tempfile.TemporaryDirectory() as tmp_dir:
            # generate the name for the file
            test_name = os.path.join(tmp_dir, "test.wav")
            # set up radio interface to expect the start signal
            ri.ptt_delay(1, use_signal=True)
            # play/record audio
            ap.play_record(audio, test_name)

            state = ri.waitState()

            ri.ptt(False)

        self.assertEqual(state, "Idle")

    def test_chan_move(self):

        fs_dev = int(48e3)

        audio_file = io.BytesIO(
            pkgutil.get_data("mcvqoe.hardware", "audio_clips/test.wav")
        )
        fs_file, audio_dat = scipy.io.wavfile.read(audio_file)

        # Calculate resample factors
        rs_factor = Fraction(fs_dev / fs_file)
        # Convert to float sound array
        audio_dat = mcvqoe.audio_float(audio_dat)
        # Resample audio
        audio = scipy.signal.resample_poly(
            audio_dat, rs_factor.numerator, rs_factor.denominator
        )

        ap = mcvqoe.hardware.AudioPlayer(
            fs=fs_dev,
            rec_chans={"rx_voice": 2, "PTT_signal": 1},
            playback_chans={"tx_voice": 2, "start_signal": 1},
        )

        with mcvqoe.hardware.RadioInterface() as ri, tempfile.TemporaryDirectory() as tmp_dir:
            # generate the name for the file
            test_name = os.path.join(tmp_dir, "test.wav")
            # set up radio interface to expect the start signal
            ri.ptt_delay(1, use_signal=True)
            # play/record audio
            ap.play_record(audio, test_name)

            state = ri.waitState()

            ri.ptt(False)

        self.assertEqual(state, "Idle")


if __name__ == "__main__":
    unittest.main()
