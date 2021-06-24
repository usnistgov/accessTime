import os.path
import shutil
import subprocess
import sys
import tempfile
import warnings

import mcvqoe
import numpy as np
import scipy.io.wavfile
import scipy.signal
from mcvqoe import audio_float
from mcvqoe.ITS_delay_est import active_speech_level

try:
    # try to import importlib.metadata
    from importlib.metadata import entry_points
except ModuleNotFoundError:
    # fall back to importlib_metadata
    from importlib_metadata import entry_points


class QoEsim:
    """
    Class to use for simulations.

    This class simulates the functionalities of mcvqoe.hardware.AudioPlayer and
    mcvqoe.hardware.RadioInterface.

    Parameters
    ----------
    port : str
        For compatibility with 'RadioInterface'. Value has no effect on simulation.
    debug : bool, default=False
        If true, print some extra 'RadioInterface' things.
    fs : int
        Sample rate of audio in/out in samples per second.
    blocksize : int
        For compatibility with 'AudioPlayer'. Value has no effect on simulation.
    buffersize : int
        For compatibility with 'AudioPlayer'. Value has no effect on simulation.
    overplay : float
        The number of seconds of extra audio to play/record at the end of a clip.
    rec_chans : dict
        Dictionary describing the recording. Dictionary keys must be one of
        {'rx_voice','PTT_signal'. For simulation, the value is ignored, as this
        normally represents the physical channel number. At this time QoEsim can not
        simulate 'timecode' or 'tx_beep' audio.
    playback_chans : dict
        Dictionary describing the playback channels. Dictionary keys should be
        one of {'tx_voice','start_signal'}. For simulation, the value is ignored,
        as this normally represents the physical channel number.

    Attributes
    ----------
    sample_rate : int
        Sample rate of audio in/out in samples per second.
    blocksize : int
        For compatibility with 'AudioPlayer'. Value has no effect on
        simulation.
    buffersize : int
        For compatibility with 'AudioPlayer'. Value has no effect on simulation.
    overplay : float
        The number of seconds of extra audio to play/record at the end of a clip.
    device : str
        Device name for compatibility with 'AudioPlayer'. This is set to the
        string representation of the class instance by default. Changing has no
        effect on simulations.
    rec_chans : dict
        Dictionary describing the recording. Dictionary keys must be one of
        {'rx_voice','PTT_signal'}. For simulation, the value is ignored, as this
        normally represents the physical channel number. At this time QoEsim can
        not simulate 'timecode' or 'tx_beep' audio.
    playback_chans : dict
        Dictionary describing the playback channels. Dictionary keys must be one
        of {'tx_voice','start_signal'}. The value for each entry is the, zero
        based, channel number that each signal should be played on.
    channel_tech : {'clean','p25','analog','amr-wb','amr-nb'}, default='clean'
        Technology to use for the simulated channel.
    channel_rate : int or str, default=None
        rate to simulate channel at. Each channel tech handles this differently.
        When set to None the default rate is used.
    pre_impairment : function, default=None
        Impairment function to apply before the audio goes through the channel.
        This function is passed an audio vector and should return a audio vector,
        of the same length, with the impairments applied. A value of None skips
        applying an impairment.
    post_impairment : function, default=None
        Impairment function to apply after the audio goes through the channel.
        This function is passed an audio vector and should return a audio vector,
        of the same length, with the impairments applied. A value of None skips
        applying an impairment.
    channel_impairment : function, default=None
        Imparment to apply to the channel data. This is not super well defined
        as each channel is a bit diffrent. A value of None skips applying an
        impairment.
    dvsi_path : str, default='pcnrtas'
        path to the dvsi encode/decode executable. Used to simulate P25 channels.
    fmpeg_path : str
        path to the ffmpeg executable. Ffmpeg is used to simulate for amr
        channels. By default the path is searched for ffmpeg, if the ffmpeg
        program is found on the path then this will be the full path to ffmpeg.
        Otherwise this will simply be the string 'ffmpeg'.
    m2e_latency : float, default=21.1e-3
        Simulated mouth to ear latency for the channel in seconds.
    access_delay : float, default=0
        Delay between the time that the simulated push to talk button is pushed
        and when audio starts coming through the channel. If the 'ptt_delay'
        method is called before play_record is called, then the time given to
        'ptt_delay' is added to access_delay to get the time when access is
        granted. Otherwise access is granted 'access_delay' seconds after the
        clip starts.
    rec_snr : float, default=60
        Signal to noise ratio for audio channel.
    print_args : bool, default=False
        Print arguments to external programs.
    PTT_sig_freq : float, default=409.6
        Frequency of the PTT signal from the play_record method.
    PTT_sig_aplitude : float, default=0.7
        Amplitude of the PTT signal from the play_record method.

    See Also
    --------
    mcvqoe.hardware.AudioPlayer : Play audio on real hardware.
    mcvqoe.hardware.RadioInterface : Key real radios.

    Examples
    --------
    Play 48 kHz audio stored in tx_voice and record in a file named 'test.wav'.

    >>> import mcvqoe.simulation.QoEsim
    >>> sim_obj=mcvqoe.simulation.QoEsim(fs=int(48e3))
    >>> sim_obj.play_record(tx_voice,'test.wav')

    Now do the same but also output the start signal on channel 1 and record the
    PTT signal on channel 1.

    >>> sim_obj.playback_chans={'tx_voice':0,'start_signal':1}
    >>> sim_obj.rec_chans={'rx_voice':0,'PTT_signal':1}
    >>> sim_obj.play_record(tx_voice,'test.wav')
    """

    def __init__(
        self,
        port=None,
        debug=False,
        fs=int(48e3),
        blocksize=512,
        buffersize=20,
        overplay=1.0,
        rec_chans={"rx_voice": 0},
        playback_chans={"tx_voice": 0},
    ):

        # locate any channel plugins installed
        chans = entry_points()["mcvqoe.channel"]

        self._chan_types = {}
        self._chan_mods = {}
        for c in chans:
            # add to channel dict
            self._chan_types[c.name] = c

        self.debug = debug
        self.PTT_state = [
            False,
        ] * 2
        self.LED_state = [
            False,
        ] * 2
        self.ptt_wait_delay = [
            -1.0,
        ] * 2
        # values for AudioPlayer
        self.sample_rate = fs
        self.blocksize = blocksize
        self.buffersize = buffersize
        self.overplay = overplay
        self.device = __class__  # fake device name
        self.rec_chans = rec_chans
        self.playback_chans = playback_chans
        # channel variables
        self.channel_tech = "clean"
        self.channel_rate = None
        self.pre_impairment = None
        self.post_impairment = None
        self.channel_impairment = None
        # TODO : set based on tech
        self.m2e_latency = 21.1e-3
        self.access_delay = 0
        # SNR for audio in dB
        self.rec_snr = 60
        # print arguments sent to external programs for debugging
        self.print_args = False
        # PTT signal parameters
        self.PTT_sig_freq = 409.6  # TODO : VERIFY!
        self.PTT_sig_aplitude = 0.7

    def __enter__(self):

        return self

    def ptt(self, state, num=1):
        """
        Change the push-to-talk status of the radio interface.

        For 'RadioInterface' this would turn on or off the PTT outputs. For simulation,
        This function does not have much of an effect. It will clear any PTT time set by
        the 'ptt_delay' method.

        Parameters
        ----------
        state : bool
            State to set PTT output to.
        num : int, default=1
            PTT output number to use.

        See Also
        --------
        mcvqoe.hardware.RadioInterface.ptt : Same function but, for hardware.

        Examples
        --------
        Key a fake radio.

        >>> sim_obj=mcvqoe.simulation.QoEsim()
        >>> sim_obj.ptt(True)  #key radio
        >>> sim_obj.ptt(False) #de-key radio
        """

        self.PTT_state[num] = bool(state)
        # clear wait delay
        self.ptt_wait_delay[num] = -1

    def led(self, num, state):
        """
        Turn on and off fake LEDs.

        For 'RadioInterface' this would turn on or off LEDs on the device. For simulation
        this function doesn't do much.

        Parameters
        ----------
        num : int
            LED number to set.
        state : bool
            The LED state to set. True is on, False is off.

        See Also
        --------
        mcvqoe.hardware.RadioInterface.led : Same function but, for hardware.

        Examples
        --------
        Turn on some fake LEDs.

        >>> sim_obj=mcvqoe.simulation.QoEsim()
        >>> sim_obj.led(1,True)
        >>> sim_obj.led(2,True)
        >>> sim_obj.led(1,False)
        """

        # check LED state
        if state:
            if self.debug:
                print("RadioInterface LED {%num} state is on")
        else:
            if self.debug:
                print("RadioInterface LED {%num} state is off")

        # set state in simulation object
        self.LED_state[num] = bool(state)

    def devtype(self):
        """
        Get the devicetype string from the fake radio interface.

        For 'RadioInterface' this would query the firmware version of the board.
        For simulation, this just returns a version string.

        Returns
        -------
        str
            A string pretending to come from a 'RadioInterface' board.

        See Also
        --------
        mcvqoe.hardware.RadioInterface.devtype : Same function but, for hardware.

        Examples
        --------
        Query a fake 'RadioInterface'.

        >>> sim_obj=mcvqoe.simulation.QoEsim()
        >>> print(sim_obj.devtype())
        """

        # TODO : simulate other versions??
        return "MCV radio interface : v1.2.1"

    def get_id(self):
        """
        Get the ID string from radio interface.

        For 'RadioInterface' this would query the firmware version of the board.
        For simulation, this just returns the filename.

        Returns
        -------
        str
            A string pretending to come from a 'RadioInterface' board.

        See Also
        --------
        mcvqoe.hardware.RadioInterface.get_id : Same function but, for hardware.

        Examples
        --------
        Query a fake 'RadioInterface'.

        >>> sim_obj=mcvqoe.simulation.QoEsim()
        >>> print(sim_obj.get_id())
        """

        return os.path.basename(__file__)

    def get_version(self):
        """
        Get the version string from fake 'RadioInterface'.

        For 'RadioInterface' this would query the firmware version of the board.
        For simulation, this just returns the mcvqoe library version.

        Returns
        -------
        str
            A string pretending to come from a 'RadioInterface' board.

        See Also
        --------
        mcvqoe.hardware.RadioInterface.get_version : Same function but, for hardware.

        Examples
        --------
        Query a fake 'RadioInterface'.

        >>> sim_obj=mcvqoe.simulation.QoEsim()
        >>> print(sim_obj.get_version())
        """

        return mcvqoe.version

    def pttState(self):
        """
        Get the PTT state from fake 'RadioInterface'.

        Return the state of the simulated PTT outputs.

        Returns
        -------
        bool array
            An array with the status of each simulated PTT output.

        See Also
        --------
        mcvqoe.hardware.RadioInterface.pttState : Same function but, for hardware.

        Examples
        --------
        Query a fake 'RadioInterface'.

        >>> sim_obj=mcvqoe.simulation.QoEsim()
        >>> print(sim_obj.pttState())
        >>> sim_obj.ptt(True)
        >>> print(sim_obj.pttState())
        """
        return self.PTT_state

    def waitState(self):
        """
        Get the PTT wait state from fake 'RadioInterface'.

        For 'RadioInterface' this would check if PTT outputs were waiting for a
        start signal. For simulation this always returns 'Idle'

        Returns
        -------
        str
            This function always returns 'Idle'.

        See Also
        --------
        mcvqoe.hardware.RadioInterface.waitState : Same function but, for hardware.

        Examples
        --------
        Query a fake 'RadioInterface'.

        >>> sim_obj=mcvqoe.simulation.QoEsim()
        >>> print(sim_obj.waitState())
        """

        # TODO: do we need to simulate this better?
        return "Idle"

    def ptt_delay(self, delay, num=1, use_signal=False):
        """
        Set how far into the clip to key the fake radio.

        For 'RadioInterface' this would setup the PTT output to key up with a
        specified delay. For simulation, this sets the time in the clip that
        'access_delay' is referenced to.

        Parameters
        ----------
        delay : float
            The number of seconds between the start of the clip and when the
            'access_delay' time starts counting.
        num : int, default=1
            The PTT output to use.
        use_signal : bool, default=True
            For 'RadioInterface', this would control if the start signal is used
            to reference the 'delay' to the beginning of the clip. For simulation
            'delay' is always referenced to the beginning of the clip.

        See Also
        --------
        mcvqoe.hardware.RadioInterface.ptt_delay : Same function but, for hardware.
        mcvqoe.simulation.QoEsim.play_record : Where 'delay' times are used.

        Examples
        --------
        Generate a simulated clip where the radio is keyed up 1 second into the
        clip. 'tx_voice' has the 48k Hz voice vector. The result is stored in
        'test.wav'

        >>> sim_obj=mcvqoe.simulation.QoEsim(fs=int(48e3))
        >>> sim_obj.playback_chans={'tx_voice':0,'start_signal':1}
        >>> sim_obj.rec_chans={'rx_voice':0,'PTT_signal':1}
        >>> sim_obj.ptt_delay(1)
        >>> sim_obj.play_record(tx_voice,'test.wav')
        """

        self.ptt_wait_delay[num] = delay
        # set state to true, this isn't 100% correct but the delay will be used
        # for the sim so, it shouldn't matter
        self.PTT_state[num] = True

    def temp(self):
        """
        Read fake temperatures from fake hardware.

        For 'RadioInterface' this would read temperature from the microcontroller.
        For simulation, this returns some fake values.

        Returns
        -------
        int array
            Two integers representing the internal temperature and external
            temperature.

        See Also
        --------
        mcvqoe.hardware.RadioInterface.temp : Same function but, for hardware.

        Examples
        --------
        Read some fake temperatures.

        >>> sim_obj=mcvqoe.simulation.QoEsim()
        >>> print(sim_obj.temp())
        """
        # TODO : generate better fake values??
        return (38, 1500)

    # delete method
    def __del__(self):
        # nothing to do here
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):

        self.ptt(False)
        self.led(1, False)

    # =====================[Find device function]=====================
    def find_device(self):
        """
        Return fake device name.

        For 'AudioPlayer' this would return the name of the audio device to use.
        For simulation this just returns the string representation of the class.

        Returns
        -------
        str
            The string representation of the class instance.

        See Also
        --------
        mcvqoe.hardware.AudioPlayer.find_device : Same function but for hardware.

        Examples
        --------
        Query a fake 'AudioPlayer'.

        >>> sim_obj=mcvqoe.simulation.QoEsim()
        >>> print(sim_obj.find_device())
        """
        return __class__

    # =====================[Get Channel Technologies]=====================
    def get_channel_techs(self):
        """
        Return a list of channel technologies.

        This returns a list of the channel technologies that have been found.
        These can be used as values for the `channel_tech` property.

        Returns
        -------
        list of strings
            A list of the names of channel technologies.

        See Also
        --------
        mcvqoe.simulation.QoEsim.channel_tech : Channel technology to use.
        mcvqoe.simulation.QoEsim.play_record : Function to simulate a channel.

        Examples
        --------

        List channel technologies.

        >>>sim=QoEsim()
        >>>sim.get_channel_techs()
        ["clean"]
        """
        return list(self._chan_types.keys())

    # =====================[Get Channel Rates]=====================
    def get_channel_rates(self, tech):
        """
        Return possible rates for a given channel tech.

        This queries a channel plugin for the default rate and a list of unique
        rates that can be used on the channel.

        Returns
        -------
        default_rate : string or number
            Default rate for channel, if no rate is used, None is returned.
        rates : list
            A list of the names of channel technologies. If no rate is used, an
            empty list is returned.

        See Also
        --------
        mcvqoe.simulation.QoEsim.get_channel_techs : List of channel technologies.
        mcvqoe.simulation.QoEsim.channel_tech : Channel technology to use.
        mcvqoe.simulation.QoEsim.play_record : Function to simulate a channel.

        Examples
        --------
        Get rates for a clean channel

        >>> sim=QoEsim()
        >>> sim.get_channel_techs('clean')
        (None,[])
        """
        mod = self._get_chan_mod(tech)
        return (mod.default_rate, mod.rates)

    # =====================[get channel module]=====================
    def _get_chan_mod(self, tech):
        try:
            chan_mod = self._chan_mods[tech]
        except KeyError:
            try:
                chan_info = self._chan_types[tech]
            except KeyError:
                raise ValueError(
                    f'Unknown channel tech "{tech}" valid channel technologies are {self.get_channel_techs()}'
                )

            # load module for channel
            chan_mod = chan_info.load()
            # save module for later
            # TODO : is this needed? good idea?
            self._chan_mods[self.channel_tech] = chan_mod

        return chan_mod

    # =====================[record audio function]=====================
    def play_record(self, audio, out_name):
        """
        Simulate playing and recording of audio through a communication channel.

        This function simulates a communication channel. The values in
        'self.playback_chans' are checked for valid values, but they don't really
        have any other effect. Only 'rech_chans' of type 'rx_voice' and
        'PTT_signal' can be used.

        Parameters
        ----------
        audio : array
            An array of audio data to pass through the communication channel.
        out_name : str
            The name of the output .wav file to write to.

        Returns
        -------
        list of strings
            A list of the recorded output channels in the order that they appear
            in the output file.

        See Also
        --------
        mcvqoe.hardware.AudioPlayer.play_record : Same function but for hardware.

        Examples
        --------
        Play 48 kHz audio stored in tx_voice and record in a file named
        'test.wav'.

        >>> import mcvqoe.simulation.QoEsim
        >>> sim_obj=mcvqoe.simulation.QoEsim(fs=int(48e3))
        >>> sim_obj.play_record(tx_voice,'test.wav')

        Now do the same but also output the start signal on channel 1 and record
        the PTT signal on channel 1.

        >>> sim_obj.playback_chans={'tx_voice':0,'start_signal':1}
        >>> sim_obj.rec_chans={'rx_voice':0,'PTT_signal':1}
        >>> sim_obj.play_record(tx_voice,'test.wav')
        """
        # loop through playback_chans this is mostly just a format check to make
        # sure that all keys used are valid
        for (k, v) in self.playback_chans.items():
            if k == "start_signal":
                pass
            elif k == "tx_voice":
                pass
            else:
                raise ValueError(f"Unknown output channel : {k}")

        # list of outputs that we need to produce
        outputs = []
        # loop through rec_chans and detect keys that we can't produce
        for (k, v) in self.rec_chans.items():
            if k not in ("rx_voice", "PTT_signal"):
                raise RuntimeError(f"{__class__} can not generate recordings of type '{k}'")
            outputs.append(k)

        # get the module for the chosen channel tech
        chan_mod = self._get_chan_mod(self.channel_tech)

        # get delay offset for channel technology
        m2e_offset = chan_mod.standard_delay

        # calculate values in samples
        overplay_samples = int(self.overplay * self.sample_rate)
        # correct for audio channel latency
        m2e_latency_samples = int((self.m2e_latency - m2e_offset) * self.sample_rate)

        if m2e_latency_samples < 0:
            # TODO : it might be possible to get around this but, it sounds slightly nontrivial...
            raise ValueError(
                f"Unable to simulate a latency of {self.m2e_latency}. Minimum simulated latency for technology '{self.channel_tech}' is {m2e_offset}"
            )

        # convert audio values to floats to work on them
        float_audio = mcvqoe.audio_float(audio)

        # append overplay to audio
        overplay_audio = np.zeros(int(overplay_samples), dtype=np.float32)
        tx_data_with_overplay = np.concatenate((float_audio, overplay_audio))

        if self.rec_snr is None:
            # don't add any noise
            tx_data_with_overplay_and_noise = tx_data_with_overplay
        else:
            # generate gaussian noise, of unit standard deveation
            noise = np.random.normal(0, 1, len(tx_data_with_overplay)).astype(np.float32)

            # measure amplitude of signal and noise
            sig_level = active_speech_level(tx_data_with_overplay, self.sample_rate)
            noise_level = active_speech_level(noise, self.sample_rate)

            # calculate noise gain required to get desired SNR
            noise_gain = sig_level - (self.rec_snr + noise_level)

            # set noise to the correct level
            noise_scaled = noise * (10 ** (noise_gain / 20))

            # add noise to audio
            tx_data_with_overplay_and_noise = tx_data_with_overplay + noise_scaled

        # check if PTT was keyed during audio
        if self.ptt_wait_delay[1] == -1:
            # PTT wait not set, don't simulate access time
            ptt_st_dly_samples = 0
            access_delay_samples = 0
        else:
            ptt_st_dly_samples = int(self.ptt_wait_delay[1] * self.sample_rate)
            access_delay_samples = int(self.access_delay * self.sample_rate)

        # mute portion of tx_data that occurs prior to triggering of PTT
        muted_samples = int(access_delay_samples + ptt_st_dly_samples)
        muted_tx_data_with_overplay = tx_data_with_overplay_and_noise[muted_samples:]

        # add pre channel impairments
        if self.pre_impairment:
            muted_tx_data_with_overplay = self.pre_impairment(
                muted_tx_data_with_overplay, self.sample_rate
            )

        # call audio channel function from module
        channel_voice = chan_mod.simulate_audio_channel(
            muted_tx_data_with_overplay,
            self.sample_rate,
            self.channel_rate,
            self.print_args,
            self.channel_impairment,
        )

        # add post channel impairments
        if self.post_impairment:
            channel_voice = self.post_impairment(channel_voice, self.sample_rate)

        # generate silent noise section comprised of ptt_st_dly, access delay and m2e latency audio snippets
        silence_length = int(ptt_st_dly_samples + access_delay_samples + m2e_latency_samples)

        # derive mean and standard deviation from real-world noise observed in the audio recordings
        mean = 0
        std = 1.81e-5

        silent_section = np.random.normal(mean, std, silence_length)

        # prepend silent section to rx_data
        rx_voice = np.concatenate((silent_section, channel_voice))

        # force rx_data to be the same length as tx_data_with_overplay
        rx_voice = rx_voice[: tx_data_with_overplay.shape[0]]

        # output array is the length of rx_voice x number of outputs
        rx_data = np.empty((rx_voice.shape[0], len(outputs)))

        for n, o_type in enumerate(outputs):
            if o_type == "PTT_signal":
                # calculate length of sine signal in samples
                sin_len_samples = rx_data.shape[0] - ptt_st_dly_samples
                # construct sine signal
                rx_data[ptt_st_dly_samples:, n] = self.PTT_sig_aplitude * np.sin(
                    2
                    * np.pi
                    * self.PTT_sig_freq
                    * np.arange(sin_len_samples)
                    / float(self.sample_rate)
                )
                # zero out before PTT
                rx_data[:ptt_st_dly_samples, n] = 0
            elif o_type == "rx_voice":
                # add data to the array
                rx_data[:, n] = rx_voice
            else:
                raise RuntimeError("Internal error")

        # write out audio file
        scipy.io.wavfile.write(out_name, int(self.sample_rate), rx_data)

        return outputs
