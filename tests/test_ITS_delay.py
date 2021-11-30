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

# fmt: off
expected_delay_var = {
    "F1_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((214800, 336894), (0, 3000)),
        "amrchan.amrnb": ((132624, 145104, 157584, 215184, 336894), (240, 1392, 192, 240, 3240)),
        "amrchan.amrwb": ((132624, 145104, 215184, 220944, 336894), (282, 528, 282, 3264, 3282)),
    },
    "F2_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((164880, 322776), (0, 6000)),
        "amrchan.amrnb": ((118800, 129360, 139920, 149520, 151440, 153360, 155280, 166800, 322776), (240, 192, 4800, 288, -204, -234, 12, -192, 6240)),
        "amrchan.amrwb": ((116880, 129360, 151440, 153360, 155280, 166800, 168720, 322776), (282, 384, 288, 276, 282, 0, 6486, 6282))
    },
    "M1_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((28176, 30096, 276468), (9540, 8934, 9000)),
        "amrchan.amrnb": ((30480, 32400, 105360, 120720, 134160, 276468), (9390, 9120, 9300, 8814, 6096, 9288)),
        "amrchan.amrwb": ((103440, 105360, 120720, 276468), (9282, 9360, 8976, 9282)),
    },
    "M2_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((180240, 182160, 184080, 186000, 187920, 201360, 203280, 205200, 207120, 209040, 210960, 226320, 228240, 307212), (0, 132, -882, -678, -1056, -960, -1026, -1650, -954, -972, -1752, -2784, 3840, 4278)),
        "amrchan.amrnb": ((111120, 129360, 139920, 180240, 182160, 187920, 189840, 212880, 226320, 228240, 307212), (240, 384, 1968, 240, 72, -912, -1200, -672, -2496, 864, 4596)),
        "amrchan.amrwb": ((114960, 116880, 120720, 128400, 180240, 182160, 187920, 210960, 218640, 220560, 224400, 307212), (282, 768, 384, 960, 288, -990, -864, -672, -1056, -882, 816, 4128))
    },
}

expected_delay_var_neg = {
    "F1_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((212880, 330894), (0, -3000)),
        "amrchan.amrnb": ((212880, 260880, 262800, 268560, 330894), (240, -2760, -3018, -2718, -2700)),
        "amrchan.amrwb": ((132240, 134160, 144720, 155280, 159120, 212880, 330894), (282, 336, 384, 4848, 384, 282, -2718))
    },
    "F2_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((151440, 157200, 310776), (0, -216, -6000)),
        "amrchan.amrnb": ((118800, 129360, 149520, 151440, 153360, 155280, 157200, 159120, 310776), (240, 192, 288, 234, -234, 12, 18, -1920, -5760)),
        "amrchan.amrwb": ((116880, 129360, 151440, 153360, 157200, 159120, 310776), (282, 384, 288, 276, 282, -1974, -5718))
    },
    "M1_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((20880, 258468), (0, -9000)),
        "amrchan.amrnb": ((24720, 36240, 59280, 90000, 102480, 113040, 153360, 258468), (312, -8706, -8700, -8736, -8160, -8928, -8706, -8640)),
        "amrchan.amrwb": ((24720, 26640, 74640, 90000, 102480, 161040, 180240, 258468), (282, -8880, -8718, -8670, -6768, -8718, -9216, -8736))
    },
    "M2_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((180240, 209040, 216720, 224400, 228240, 230160, 283212), (0, 960, -2688, -3552, -2292, -2322, -3234)),
        "amrchan.amrnb": ((180624, 205584, 207504, 217104, 222864, 224784, 226704, 283212), (240, 1248, 1152, -2784, -3648, -2766, -2778, -2832)),
        "amrchan.amrwb": ((113424, 130704, 136464, 180624, 182544, 205584, 207504, 211344, 213264, 219024, 283212), (282, 960, -1392, 288, 1254, 1248, -102, -1824, -3282, -2544, -3264))
    }
}

expected_delay_uknown_fix = {
    "F1_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((333894,), (0,)),
        "amrchan.amrnb": ((132624, 145104, 159504, 165264, 167184, 333894), (240, 1392, 240, 480, 66, 240)),
        "amrchan.amrwb": ((333894,), (288,))
    },
    "F2_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((316788,), (12,)),
        "amrchan.amrnb": ((316788,), (252,)),
        "amrchan.amrwb": ((316788,), (294,))
    },
    "M1_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((267570,), (102,)),
        "amrchan.amrnb": ((267570,), (390,)),
        "amrchan.amrwb": ((267570,), (384,))
    },
    "M2_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((296214,), (1002,)),
        "amrchan.amrnb": ((296214,), (1242,)),
        "amrchan.amrwb": ((296214,), (1284,))
    }
}

expected_delay_uknown_fix_neg = {
    "F1_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((333894,), (0,)),
        "amrchan.amrnb": ((132624, 145104, 333894), (240, 1392, 240)),
        "amrchan.amrwb": ((333894,), (282,))
    },
    "F2_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((130320, 316770), (-12, -6)),
        "amrchan.amrnb": ((129744, 316770), (228, 234)),
        "amrchan.amrwb": ((316770,), (276,))
    },
    "M1_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((267372,), (-96,)),
        "amrchan.amrnb": ((267372,), (192,)),
        "amrchan.amrwb": ((267372,), (186,))
    },
    "M2_harvard_phrases.wav": {
        "mcvqoe.simulation.cleanchan": ((294216,), (-996,)),
        "amrchan.amrnb": ((294216,), (-714,)),
        "amrchan.amrwb": ((294216,), (-714,))
    }
}

expected_speech_levels = {
    "amr-nb": -28.767441851923834,
    "amr-wb": -27.13075819308672,
    "clean": -25.56647986754328,
}
# fmt: on


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

    def test_basic_variable_delay(self):
        for chan in channels:
            chan = chan.load()

            for i, audio_file in enumerate(os.scandir(os.path.join(os.path.dirname(__file__), "data/ITS_general"))):
                base_fs, base_data = scipy.io.wavfile.read(audio_file)
                base_data = mcvqoe.base.misc.audio_float(base_data)

                dly = 3000 * (i + 1)
                max_loc = np.argmax(base_data) + 50

                audio_var_delay = np.concatenate(
                    (base_data[:max_loc], np.zeros([dly], dtype=np.float64), base_data[max_loc:])
                )

                chan_out = audio_channel_with_overplay(base_fs, audio_var_delay, chan)
                delay_calc = mcvqoe.delay.ITS_delay_est(base_data, chan_out, "v", fs=base_fs)

                self.assertEqual(
                    delay_calc,
                    expected_delay_var[audio_file.name][chan.__name__],
                    msg=f"{audio_file.name}: {chan.__name__}, delay: {dly} samples at position {max_loc}",
                )

                audio_var_delay = np.concatenate((base_data[:max_loc], base_data[max_loc + dly :]))
                chan_out = audio_channel_with_overplay(base_fs, audio_var_delay, chan)
                delay_calc = mcvqoe.delay.ITS_delay_est(base_data, chan_out, "v", fs=base_fs)

                self.assertEqual(
                    delay_calc,
                    expected_delay_var_neg[audio_file.name][chan.__name__],
                    msg=f"{audio_file.name}: {chan.__name__}, delay: {-dly} samples at position {max_loc}",
                )

    def test_basic_unknown_delay(self):
        for chan in channels:
            chan = chan.load()

            for i, audio_file in enumerate(os.scandir(os.path.join(os.path.dirname(__file__), "data/ITS_general"))):
                base_fs, base_data = scipy.io.wavfile.read(audio_file)
                base_data = mcvqoe.base.misc.audio_float(base_data)

                dly = 10 ** i
                audio_fixed_delay = np.concatenate((np.zeros([dly], dtype=base_data.dtype), base_data))
                chan_out = audio_channel_with_overplay(base_fs, audio_fixed_delay, chan)

                delay_calc = mcvqoe.delay.ITS_delay_est(base_data, chan_out, "u", fs=base_fs)
                self.assertEqual(
                    delay_calc,
                    expected_delay_uknown_fix[audio_file.name][chan.__name__],
                    msg=f"{audio_file.name}: {chan.__name__}, delay: {dly} samples (fixed)",
                )

                audio_fixed_delay = base_data[dly:]

                chan_out = audio_channel_with_overplay(base_fs, audio_fixed_delay, chan)

                delay_calc = mcvqoe.delay.ITS_delay_est(base_data, chan_out, "u", fs=base_fs)

                self.assertEqual(
                    delay_calc,
                    expected_delay_uknown_fix_neg[audio_file.name][chan.__name__],
                    msg=f"{audio_file.name}: {chan.__name__}, delay: {-dly} samples (fixed)",
                )

                dly = 3000 * (i + 1)
                max_loc = np.argmax(base_data) + 50

                audio_var_delay = np.concatenate(
                    (base_data[:max_loc], np.zeros([dly], dtype=np.float64), base_data[max_loc:])
                )

                chan_out = audio_channel_with_overplay(base_fs, audio_var_delay, chan)
                delay_calc = mcvqoe.delay.ITS_delay_est(base_data, chan_out, "u", fs=base_fs)

                self.assertEqual(
                    delay_calc,
                    expected_delay_var[audio_file.name][chan.__name__],
                    msg=f"{audio_file.name}: {chan.__name__}, delay: {dly} samples at position {max_loc}",
                )

                audio_var_delay = np.concatenate((base_data[:max_loc], base_data[max_loc + dly :]))
                chan_out = audio_channel_with_overplay(base_fs, audio_var_delay, chan)
                delay_calc = mcvqoe.delay.ITS_delay_est(base_data, chan_out, "u", fs=base_fs)

                self.assertEqual(
                    delay_calc,
                    expected_delay_var_neg[audio_file.name][chan.__name__],
                    msg=f"{audio_file.name}: {chan.__name__}, delay: {-dly} samples at position {max_loc}",
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
