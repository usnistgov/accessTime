import io
import pkgutil
import unittest
from math import exp

import mcvqoe
import numpy as np
import scipy
from mcvqoe.ITS_delay_est import active_speech_level

audio_files = ["test.wav", "test_nb_12200.wav", "test_wb_23850.wav"]
expected_speech_level = [-29.079965170524318, -31.12585881587833, -30.115341804098797]


def load_audio_file(name):
    audio_file = pkgutil.get_data("mcvqoe", "audio_clips/" + name)
    audio_file = io.BytesIO(audio_file)
    return scipy.io.wavfile.read(audio_file)


class ITSTest(unittest.TestCase):
    def test_basic_no_delay(self):
        for name in audio_files:
            audio_fs, audio_data = load_audio_file(name)
            audio_data = np.concatenate((np.zeros([1], dtype=np.int16), audio_data))

            expected_length = len(audio_data)
            expected_length = expected_length - (expected_length % 2) - 2

            self.assertEqual(
                mcvqoe.ITS_delay_est(audio_data, audio_data, "f", fs=audio_fs),
                (expected_length, 0),
                msg=name,
            )

            self.assertEqual(
                mcvqoe.ITS_delay_est(audio_data, audio_data, "v", fs=audio_fs),
                ((expected_length,), (0,)),
                msg=name,
            )

            self.assertEqual(
                mcvqoe.ITS_delay_est(audio_data, audio_data, "u", fs=audio_fs),
                ((expected_length,), (0,)),
                msg=name,
            )

    def test_basic_fixed_delay(self):
        for name in audio_files:
            audio_fs, audio_data = load_audio_file(name)

            audio_fixed_delay = np.concatenate(
                (np.zeros([20], dtype=np.int16), audio_data)
            )
            expected_length = len(audio_data)
            expected_length = expected_length - (expected_length % 2) + 18
            self.assertEqual(
                mcvqoe.ITS_delay_est(audio_data, audio_fixed_delay, "f", fs=audio_fs),
                (expected_length, 20),
                msg=name,
            )

            expected_length = len(audio_data) - 5
            expected_length = expected_length - (expected_length % 2) - 2
            self.assertEqual(
                mcvqoe.ITS_delay_est(audio_data, audio_data[5:], "f", fs=audio_fs),
                (expected_length, -6 + (len(audio_data) % 2 * 2)),
                msg=name,
            )

    def test_basic_variable_delay(self):
        for name in audio_files:
            audio_fs, audio_data = load_audio_file(name)

            audio_var_delay = np.concatenate(
                (
                    audio_data[5:10000],
                    np.zeros([100], dtype=np.int16),
                    audio_data[10000:],
                )
            )
            expected_length = len(audio_var_delay)
            expected_length = expected_length - (expected_length % 2) - 2
            self.assertEqual(
                mcvqoe.ITS_delay_est(audio_data, audio_var_delay, "v", fs=audio_fs),
                (
                    (8368, expected_length),
                    (-6 + (len(audio_data) % 2 * 2), 94 + (len(audio_data) % 2 * 2)),
                ),
                msg=name,
            )

    def test_basic_unknown_delay(self):
        for name in audio_files:
            audio_fs, audio_data = load_audio_file(name)

            audio_fixed_delay = np.concatenate(
                (np.zeros([20], dtype=np.int16), audio_data)
            )
            expected_length = len(audio_fixed_delay)
            expected_length = expected_length - (expected_length % 2) - 2
            self.assertEqual(
                mcvqoe.ITS_delay_est(audio_data, audio_fixed_delay, "u", fs=audio_fs),
                ((expected_length,), (20,)),
                msg=name,
            )

            audio_var_delay = np.concatenate(
                (
                    audio_data[5:10000],
                    np.zeros([100], dtype=np.int16),
                    audio_data[10000:],
                )
            )
            expected_length = len(audio_var_delay)
            expected_length = expected_length - (expected_length % 2) - 2
            self.assertEqual(
                mcvqoe.ITS_delay_est(audio_data, audio_var_delay, "u", fs=audio_fs),
                (
                    (8368, expected_length),
                    (-6 + (len(audio_data) % 2 * 2), 94 + (len(audio_data) % 2 * 2)),
                ),
                msg=name,
            )

    def test_active_speech_level(self):
        for i, name in enumerate(audio_files):
            audio_fs, audio_data = load_audio_file(name)

            self.assertEqual(
                active_speech_level(audio_data, fs=audio_fs), expected_speech_level[i]
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
