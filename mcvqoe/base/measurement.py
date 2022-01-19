import csv
import datetime
import os
import json
import shutil
import time

import numpy as np

from itertools import cycle
from mcvqoe.timing import require_timecode
from .misc import audio_write
from .naming import get_meas_basename
from .write_log import fill_log, pre as log_pre, post as log_post

class Measure:

    no_log = ()

    def run(self):
        if self.test == "1loc":
            return self.run_1loc()
        elif self.test == "2loc_tx":
            return self.run_2loc_tx()
        elif self.test == "2loc_rx":
            return self.run_2loc_rx()
        else:
            raise ValueError(f'Unknown test type "{self.test}"')

    def run_2loc_tx(self):
        """
        Run a two location test. This is a generic test function for tests like
        m2e, PSuD and Intelligibility.
        """

        # ------------------[Check for correct audio channels]------------------
        if "tx_voice" not in self.audio_interface.playback_chans.keys():
            raise ValueError("self.audio_interface must be set up to play tx_voice")
        # we need to be recording a timecode
        require_timecode(self.audio_interface)
        # -------------------------[Get Test Start Time]-------------------------

        self.info["Tstart"] = datetime.datetime.now()
        dtn = self.info["Tstart"].strftime("%d-%b-%Y_%H-%M-%S")

        # --------------------------[Fill log entries]--------------------------
        # set test name, needs to match log_search.datafilenames
        self.info["test"] = "Tx Two Loc Test"
        # fill in standard stuff
        self.info.update(fill_log(self))

        # -----------------------[Setup Files and folders]-----------------------

        # generate data dir names
        data_dir = os.path.join(self.outdir, "data")
        tx_dat_fold = os.path.join(data_dir, "2loc_tx-data")

        # generate base file name to use for all files
        base_filename = "capture_%s_%s" % (self.info["Test Type"], dtn)

        wavdir = os.path.join(tx_dat_fold, "Tx_" + base_filename)

        # create directories
        os.makedirs(wavdir, exist_ok=True)

        # Put .csv files in wav dir
        csv_data_dir = wavdir

        # generate csv name
        self.data_filename = os.path.join(csv_data_dir, f"{base_filename}.csv")

        # generate temp csv name
        temp_data_filename = os.path.join(csv_data_dir, f"{base_filename}_TEMP.csv")

        # ---------------------[Load Audio Files if Needed]---------------------

        if not hasattr(self, "y"):
            self.load_audio()

        # generate clip index
        self.clipi = self.rng.permutation(self.trials) % len(self.y)

        # -----------------------[Add Tx audio to wav dir]-----------------------

        # get name with out path or ext
        clip_names = [os.path.basename(os.path.splitext(a)[0]) for a in self.audio_files]

        if hasattr(self, 'cutpoints'):
            cutpoints = self.cutpoints
        else:
            #placeholder for zip
            cutpoints = cycle((None,))

        # write out Tx clips to files
        for dat, name, cp in zip(self.y, clip_names, cutpoints):
            out_name = os.path.join(wavdir, f"Tx_{name}")
            audio_write(out_name + ".wav", int(self.audio_interface.sample_rate), dat)
            #write cutpoints, if present
            if cp:
                mcvqoe.base.write_cp(out_name+'.csv',cp)

        # -------------------------[Generate CSV header]-------------------------

        header, dat_format = self.csv_header_fmt()

        # ---------------------------[write log entry]---------------------------

        log_pre(info=self.info, outdir=self.outdir)

        # ---------------[Try block so we write notes at the end]---------------
        try:

            # -----------------------[write initial csv file]-----------------------
            with open(temp_data_filename, "wt") as f:
                f.write(header)

            # -------------------------[Turn on RI LED]-------------------------

            self.ri.led(1, True)

            # ------------------------[Measurement Loop]------------------------

            for trial in range(self.trials):

                # -----------------------[Update progress]-------------------------
                if not self.progress_update("test", self.trials, trial):
                    # turn off LED
                    self.ri.led(1, False)
                    print("Exit from user")
                    break
                # -----------------------[Get Trial Timestamp]-----------------------
                ts = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")

                # --------------------[Key Radio and play audio]--------------------

                # Press the push to talk button
                self.ri.ptt(True)

                # Pause the indicated amount to allow the radio to access the system
                time.sleep(self.ptt_wait)

                clip_index = self.clipi[trial]

                # Create audiofile name/path for recording
                audioname = f"Rx{trial+1}_{clip_names[clip_index]}.wav"
                audioname = os.path.join(wavdir, audioname)

                # Play/Record
                rec_chans = self.audio_interface.play_record(self.y[clip_index], audioname)

                # Release the push to talk button
                self.ri.ptt(False)

                # -----------------------[Pause Between runs]-----------------------

                time.sleep(self.ptt_gap)

                # --------------------------[Write CSV]--------------------------

                chan_str = "(" + (";".join(rec_chans)) + ")"

                with open(temp_data_filename, "at") as f:
                    f.write(
                        dat_format.format(
                            Timestamp=ts,
                            Filename=clip_names[clip_index],
                            m2e_latency=np.NaN,
                            channels=chan_str,
                        )
                    )

            # -----------------------------[Cleanup]-----------------------------

            # move temp file to real file
            shutil.move(temp_data_filename, self.data_filename)

            # ---------------------------[Turn off RI LED]---------------------------

            self.ri.led(1, False)

            # -----------------------[Notify User of Completion]------------------------

            self.progress_update(
                "status",
                self.trials,
                self.trials,
                msg="Data collection complete, you may now stop data collection on" + " the receiving end",
            )

        finally:
            if self.get_post_notes:
                # get notes
                info = self.get_post_notes()
            else:
                info = {}
            # finish log entry
            log_post(outdir=self.outdir, info=info)

    def run_2loc_rx(self):
        """
        Two location recive basic test.

        This function just records audio with a little bit of logging. Should be
        usable by all 2 location tests.
        """

        # ------------------[Check for correct audio channels]------------------
        if "rx_voice" not in self.audio_interface.rec_chans.keys():
            raise ValueError("self.audio_interface must be set up to record rx_voice")
        # we need to be recording a timecode
        require_timecode(self.audio_interface)

        # -------------------------[Get Test Start Time]-------------------------
        self.info["Tstart"] = datetime.datetime.now()
        dtn = self.info["Tstart"].strftime("%d-%b-%Y_%H-%M-%S")

        # --------------------------[Fill log entries]--------------------------

        # set test name, needs to match log_search.datafilenames
        self.info["test"] = "Rx Two Loc Test"
        # fill in standard stuff
        self.info.update(fill_log(self))

        # -----------------------[Setup Files and folders]-----------------------

        # Create rx-data folder
        data_dir = os.path.join(self.outdir, "data")
        rx_dat_fold = os.path.join(data_dir, "2loc_rx-data")
        os.makedirs(rx_dat_fold, exist_ok=True)

        base_filename = "capture_%s_%s" % (self.info["Test Type"], dtn)

        self.data_filename = os.path.join(rx_dat_fold, "Rx_" + base_filename + ".wav")

        info_name = os.path.join(rx_dat_fold, "Rx_" + base_filename + ".json")

        # ---------------------------[write log entry]---------------------------

        log_pre(info=self.info, outdir=self.outdir)

        # ---------------[Try block so we write notes at the end]---------------
        try:
            # ----------------------[Send progress update]---------------------
            self.progress_update("status", 1, 0, msg="Two location receive recording running")

            # --------------------------[Record audio]--------------------------
            rec_names = self.audio_interface.record(self.data_filename)

            # ------------------------[Save audio info]------------------------

            with open(info_name, "wt") as info_f:
                json.dump({"channels": rec_names}, info_f)

        finally:
            if self.get_post_notes:
                # get notes
                info = self.get_post_notes()
            else:
                info = {}
            # finish log entry
            log_post(outdir=self.outdir, info=info)

    def load_test_data(self, fname, load_audio=True, audio_path=None):
        """
        load test data from .csv file.

        Parameters
        ----------
        fname : string
            filename to load
        load_audio : bool, default=True
            if True, finds and loads audio clips and cutpoints based on fname
        audio_path : str, default=None
            Path to find audio files at. Guessed from fname if None.

        Returns
        -------
        list of dicts
            returns data from the .csv file

        """

        with open(fname, "rt") as csv_f:
            # create dict reader
            reader = csv.DictReader(csv_f)
            print(f"reader header: {reader.fieldnames}")
            # create empty list
            data = []
            # create set for audio clips
            clips = set()
            for row in reader:
                # convert values proper datatype
                for k in row:
                    # check for clip name
                    if k == "Filename":
                        # save clips
                        clips.add(row[k])
                    try:
                        # check for None field
                        if row[k] == "None":
                            # handle None correcly
                            row[k] = None
                        else:
                            # convert using function from data_fields
                            row[k] = self.data_fields[k](row[k])
                    except KeyError:
                        # not in data_fields, convert to float
                        row[k] = float(row[k])

                # append row to data
                data.append(row)

        # set total number of trials, this gives better progress updates
        self.trials = len(data)

        # check if we should load audio
        if load_audio:
            print(f"clips : {clips}")
            # set audio file names to Tx file names
            self.audio_files = ["Tx_" + name + ".wav" for name in clips]

            dat_name = get_meas_basename(fname)

            if audio_path is not None:
                self.audio_path = audio_path
            else:
                # set audio_path based on filename
                self.audio_path = os.path.join(os.path.dirname(os.path.dirname(fname)), "wav", dat_name)

            # load audio data from files
            self.load_audio()
            # self.audio_clip_check()

        return data

    # get the clip index given a partial clip name
    def find_clip_index(self, name):
        """
        find the inex of the matching transmit clip.

        Parameters
        ----------
        name : string
            base name of audio clip

        Returns
        -------
        int
            index of matching tx clip

        """

        # match a string that has the chars that are in name
        name_re = re.compile(re.escape(name) + "(?![^.])")
        # get all matching indices
        match = [idx for idx, clip in enumerate(self.audio_files) if name_re.search(clip)]
        # check that a match was found
        if not match:
            raise RuntimeError(f"no audio clips found matching '{name}' found in {self.audio_files}")
        # check that only one match was found
        if len(match) != 1:
            raise RuntimeError(f"multiple audio clips found matching '{name}' found in {self.audio_files}")
        # return matching index
        return match[0]

    def post_process(self, test_dat, fname, audio_path):
        """
        process csv data.

        Parameters
        ----------
        test_data : list of dicts
            csv data for trials to process
        fname : string
            file name to write processed data to
        audio_path : string
            where to look for recorded audio clips

        Returns
        -------

        """

        # get .csv header and data format
        header, dat_format = self.csv_header_fmt()

        with open(fname, "wt") as f_out:

            f_out.write(header)

            for n, trial in enumerate(test_dat):

                # update progress
                self.progress_update("proc", self.trials, n)

                # find clip index
                clip_index = self.find_clip_index(trial["Filename"])
                # create clip file name
                clip_name = "Rx" + str(n + 1) + "_" + trial["Filename"] + ".wav"

                try:
                    # attempt to get channels from data
                    rec_chans = trial["channels"]
                except KeyError:
                    # fall back to only one channel
                    rec_chans = ("rx_voice",)
                new_dat = self.process_audio(clip_index, os.path.join(audio_path, clip_name), rec_chans)

                # overwrite new data with old and merge
                merged_dat = {**trial, **new_dat}

                # write line with new data
                f_out.write(dat_format.format(**merged_dat))
