import io
import os
import pkgutil
import unittest

import mcvqoe.delay
import numpy as np
import scipy.io.wavfile
import xmlrunner
from mcvqoe.delay.ITS_delay import active_speech_level

try:
    # try to import importlib.metadata
    from importlib.metadata import entry_points
except ModuleNotFoundError:
    # fall back to importlib_metadata
    from importlib_metadata import entry_points

channels = entry_points()["mcvqoe.channel"]

expected_speech_levels = {
    "amr-nb": -28.767441851923834,
    "amr-wb": -27.13075819308672,
    "clean": -25.56647986754328,
}


def audio_channel_with_overplay(audio_fs, audio_data, chan):
    audio_with_overplay = np.concatenate((audio_data, np.zeros([audio_fs], dtype=audio_data.dtype)))
    chan_out = chan.simulate_audio_channel(audio_with_overplay, audio_fs)
    chan_out = chan_out[: len(audio_with_overplay)]
    return chan_out


class ITSTest(unittest.TestCase):
    def assert_tol(self, x, y, tol=0, msg=None):
        self.assertGreaterEqual(x, y - tol, msg)
        self.assertLessEqual(x, y + tol, msg)

    def test_basic_no_delay(self):
        for audio_file in os.scandir(os.path.join(os.path.dirname(__file__), "data/ITS_general")):
            base_fs, base_data = scipy.io.wavfile.read(audio_file)

            for chan in channels:
                chan = chan.load()
                chan_out = audio_channel_with_overplay(base_fs, base_data, chan)

                expected_length = len(base_data) + base_fs
                expected_delay = int(chan.standard_delay * base_fs)

                delay_calc = mcvqoe.delay.ITS_delay_est(base_data, chan_out, "f", fs=base_fs)

                self.assert_tol(delay_calc[0], expected_length, tol=15, msg=chan.__name__)
                self.assert_tol(delay_calc[1], expected_delay, tol=40, msg=chan.__name__)

    def test_basic_fixed_delay(self):
        for chan in channels:
            chan = chan.load()

            for i, audio_file in enumerate(os.scandir(os.path.join(os.path.dirname(__file__), "data/ITS_general"))):
                base_fs, base_data = scipy.io.wavfile.read(audio_file)
                base_data = mcvqoe.base.misc.audio_float(base_data)

                dly = 10 ** i
                audio_fixed_delay = np.concatenate((np.zeros([dly], dtype=base_data.dtype), base_data))
                chan_out = audio_channel_with_overplay(base_fs, audio_fixed_delay, chan)

                expected_length = len(audio_fixed_delay) + base_fs

                expected_delay = int(chan.standard_delay * base_fs) + dly

                delay_calc = mcvqoe.delay.ITS_delay_est(base_data, chan_out, "f", fs=base_fs)

                self.assert_tol(
                    delay_calc[0],
                    expected_length,
                    tol=15,
                    msg=f"{chan.__name__}, delay: {dly} samples",
                )
                self.assert_tol(
                    delay_calc[1],
                    expected_delay,
                    tol=40,
                    msg=f"{chan.__name__}, delay: {dly} samples",
                )

                audio_fixed_delay = base_data[dly:]

                chan_out = audio_channel_with_overplay(base_fs, audio_fixed_delay, chan)

                expected_length = len(audio_fixed_delay) + base_fs
                expected_delay = int(chan.standard_delay * base_fs) - dly

                delay_calc = mcvqoe.delay.ITS_delay_est(base_data, chan_out, "f", fs=base_fs)
                self.assert_tol(
                    delay_calc[0],
                    expected_length,
                    tol=15,
                    msg=f"{chan.__name__}, delay: {dly} samples",
                )
                self.assert_tol(
                    delay_calc[1],
                    expected_delay,
                    tol=40,
                    msg=f"{chan.__name__}, delay: {dly} samples",
                )

    def test_low_info(self):
        dir = os.path.dirname(__file__)
        base_fs, tx_data = scipy.io.wavfile.read(os.path.join(dir, "data/ITS_low_info/Tx_M3_n10_s1_c21.wav"))
        _, rx_data = scipy.io.wavfile.read(os.path.join(dir, "data/ITS_low_info/Rx1_M3_n10_s1_c22.wav"))

        tx_data = mcvqoe.base.misc.audio_float(tx_data)
        rx_data = mcvqoe.base.misc.audio_float(rx_data)

        self.assertEqual(mcvqoe.delay.ITS_delay_est(tx_data, rx_data, "f", fs=base_fs, min_corr=0.76), (0, 0))

    def test_active_speech_level(self):
        base_file = pkgutil.get_data("mcvqoe.audio_clips", "test.wav")
        base_file = io.BytesIO(base_file)
        base_fs, base_data = scipy.io.wavfile.read(base_file)

        for i, chan in enumerate(channels):
            chan_l = chan.load()

            chan_out = audio_channel_with_overplay(base_fs, base_data, chan_l)
            chan_out = mcvqoe.base.misc.audio_type(chan_out)
            self.assert_tol(
                active_speech_level(chan_out, fs=base_fs),
                expected_speech_levels[chan.name],
                tol=0.1,
                msg=f"{chan.name}, no delay",
            )

            audio_var_delay = np.concatenate(
                (
                    base_data[:50000],
                    np.zeros([20000], dtype=np.int16),
                    base_data[50000:],
                )
            )

            chan_out = audio_channel_with_overplay(base_fs, audio_var_delay, chan_l)
            chan_out = mcvqoe.base.misc.audio_type(chan_out)
            self.assert_tol(
                active_speech_level(chan_out, fs=base_fs),
                expected_speech_levels[chan.name],
                tol=0.1,
                msg=f"{chan.name}, 20000 samples delay at position 100000",
            )


if __name__ == "__main__":
    with open("ITS-tests.xml", "wb") as outf:
        unittest.main(
            testRunner=xmlrunner.XMLTestRunner(output=outf),
            failfast=False,
            buffer=False,
            catchbreak=False,
        )
