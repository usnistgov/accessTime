#!/usr/bin/env python

import csv
import glob
import json
import mcvqoe.base
import os
import re
import shutil

import numpy as np

from .audio_chans import timecode_chans
from datetime import datetime, timedelta
from .timecode import time_decode
from warnings import warn


def test_name_parts(name):
    m=re.match( r'(?P<prefix>.*capture)_'+
                    '(?P<testtype>.+)_'+
                    '(?P<date>\d{2}-\w{3}-\d{4}_\d{2}-\d{2}-\d{2})'+
                    '(?P<ext>\.\w+)?$',
                name
              )
    return (m.group('prefix'),m.group('testtype'),m.group('date'))

def twoloc_process(tx_name, extra_play=0, rx_name = None, outdir="", audio_type=np.dtype('int16')):
    '''
    Process rx and tx files for a two location test.
    
    This writes a .csv file to data/csv and wave files to data/wav for a test. 

    Parameters
    ----------
    tx_name : string
        path to the transmit .csv file. If this is a relative path than
        `[outdir]/data/csv` is searched.
    extra_play : float, default=0
        Extra audio to add after tx clip stopped. This mayb be used, in some
        cases, to correct for data that was recorded with a poorly chosen
        overplay.
    rx_name : string, None
        Name of the receive .wav file. If this is a relative path than
        `[outdir]/data/csv` is searched. If this is None then `data/2loc_rx-data`
        is searched.
    outdir : string, default=""
        Directory that contains the `data/` folder where data will be read from
        and written to.
    audio_type : np.dtype, default=np.dtype('int16')
        Type of data to save .wav files as. 
        
    See Also
    --------
        mcvqoe.mouth2ear : mouth to ear code, can produce 2 location data.
    '''

    #This software was developed by employees of the National Institute of
    #Standards and Technology (NIST), an agency of the Federal Government.
    #Pursuant to title 17 United States Code Section 105, works of NIST
    #employees are not subject to copyright protection in the United States and
    #are considered to be in the public domain. Permission to freely use, copy,
    #modify, and distribute this software and its documentation without fee is
    #hereby granted, provided that this notice and disclaimer of warranty
    #appears in all copies.
    #
    #THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND, EITHER
    #EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY
    #WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED
    #WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND
    #FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION WILL
    #CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE ERROR
    #FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING, BUT NOT
    #LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES, ARISING
    #OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS SOFTWARE,
    #WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR OTHERWISE, WHETHER
    #OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY OR OTHERWISE, AND
    #WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT OF THE RESULTS OF, OR
    #USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
   
    #-----------------------------Validate inputs-----------------------------

    tx_wav_path=os.path.dirname(tx_name)

    #get folder name (just name, no path)
    tx_wav_fold =  os.path.basename(tx_wav_path)
    
    #extract parts of tx name for validation
    (tx_prefix,tx_tt,tx_date)=test_name_parts(tx_wav_fold)
    #check prefix
    if(tx_prefix != 'Tx_capture'):
        raise ValueError(f'Unexpected filename prefix \'{tx_prefix}\' for tx file')
    
    #extra_play must be non-neg
    if extra_play < 0:
        raise ValueError("extra_play must be non negative")

    #tolerence for timecode variation
    tc_warn_tol = 0.0001

    # --------------------------[Locate input data]--------------------------
    
    #go two levels up from .csv file
    tx_fold=os.path.dirname(os.path.dirname(tx_name))
    
    indir=os.path.abspath(os.path.join(tx_fold,'..','..'))
    
    rx_dir=os.path.join(indir,'data','2loc_rx-data')

    # -----------------------[Setup Files and folders]-----------------------

    # generate data dir names
    data_dir = os.path.join(outdir, "data")
    wav_data_dir = os.path.join(data_dir, "wav")
    csv_data_dir = os.path.join(data_dir, "csv")

    # create data directories
    os.makedirs(csv_data_dir, exist_ok=True)
    os.makedirs(wav_data_dir, exist_ok=True)

    # generate base file name to use for all files
    base_filename ='_'.join(('capture2',tx_tt,tx_date))

    # generate test dir names
    wavdir = os.path.join(wav_data_dir, base_filename)

    # create test dir
    os.makedirs(wavdir, exist_ok=True)

    # generate csv name
    csv_out_name = os.path.join(csv_data_dir, f"{base_filename}.csv")
    
    #------------------Find appropriate rx file by timecode------------------
    #if a rx file name is not specified, find the appropriate file in rx-dat 
    #folder. if there are more than one suitable rx files based on timecode, 
    #this will find the one with the smallest delay, with delay defined as 
    #difference between the start times of the rx and tx recordings
    
    #if no file was specified for the rx file, search for it in rx-dat
    if not rx_name:
    
        #attempt to get date from tx filename
        tx_date=datetime.strptime(tx_date, '%d-%b-%Y_%H-%M-%S')
        
        #rx_files is a dict with the delays as keys, and the rx path as values
        rx_files = {}
        print(f'looking for rx files in \'{rx_dir}\'')
        #loop thru all rx files
        for rx_file_name in glob.glob(os.path.join(rx_dir,'*.wav')):
            print(f'Looking at {rx_file_name}')
            #strip leading folders
            rx_basename=os.path.basename(rx_file_name)
            #split into parts
            (rx_prefix,rx_tt,rx_date)=test_name_parts(rx_basename)
            #validate that this is a correct rx file
            if rx_prefix != 'Rx_capture':
                #give error
                warn('Rx filename "%s" is not in the proper form. Can not determine Rx filename' %rx_file_name)
                #if not a correct rx file, skip this file and go to next one
                continue
            rx_start_date=datetime.strptime(rx_date, '%d-%b-%Y_%H-%M-%S')
            #add to the rx_file dict, with delays as the key, and full path as value
            rx_files[tx_date - rx_start_date] = rx_file_name
    
        #create a np array of all of delays
        delays = np.array(list(rx_files), dtype=timedelta)
        
        #find the smallest positive delay
        minDelay = min(delays[delays > timedelta()])
        
        #find the file with the the smallest delay
        rx_name=rx_files[minDelay]
        #read file
        rx_fs, rx_dat = mcvqoe.base.audio_read(rx_name)
    
        #find the duration of the rx file
        duration = timedelta(seconds=len(rx_dat)/rx_fs)
        
        #check that tx date falls within rx file time
        if minDelay < duration:
            rx_name = rx_files[minDelay]
        #otherwise there is no suitable rx file
        else:
            raise ValueError("Could not find suitable Rx file")
    
    else:
        rx_fs, rx_dat = mcvqoe.base.audio_read(rx_name)
    
    rx_dat=mcvqoe.base.audio_float(rx_dat)
    
    #--------------------Prep work for calculating delays--------------------

    rx_info_name=os.path.splitext(rx_name)[0]+'.json'
    
    with open(rx_info_name) as info_f:
        rx_info=json.load(info_f)
        
    tc_chans=timecode_chans(rx_info['channels'])
    if not tc_chans:
        raise ValueError(f'Timecode channel could not be found in {rx_info["channels"]}')
    
    #use the first one
    rx_tc_idx=tc_chans[0]
    
    #timecode type
    rx_tc_type=rx_info['channels'][rx_tc_idx]
    
    #get channels
    rx_extra_chans=rx_info['channels']
    #remove timecode channel
    del rx_extra_chans[rx_tc_idx]
    
    #decode the rx timecode
    rx_time, rx_snum = time_decode(rx_tc_type,rx_dat[:,rx_tc_idx], rx_fs)
    
    #make rx_time a numpy array
    rx_time = np.array(rx_time)

    extra_samples = extra_play * rx_fs
    with open(tx_name,'rt') as tx_csv_f, open(csv_out_name,'wt') as out_csv_f:
        
        #create dict reader
        reader=csv.DictReader(tx_csv_f)
        
        #create dict writer, same fields as input
        writer=csv.DictWriter(out_csv_f,reader.fieldnames)
        
        #write output header
        writer.writeheader()
    
        #loop thru all tx recordings
        for trial,row in enumerate(reader):
            tx_rec_name = f'Rx{trial+1}_{row["Filename"]}.wav'
            full_tx_rec_name = os.path.join(tx_wav_path, tx_rec_name)
            tx_rec_fs, tx_rec_dat = mcvqoe.base.audio_read(full_tx_rec_name)
            #make floating point for processing purposes
            tx_rec_dat=mcvqoe.base.audio_float(tx_rec_dat)
            
            tx_rec_chans=mcvqoe.base.parse_audio_channels(row['channels'])
            
            if(len(tx_rec_chans)==1):
                #only one channel, make sure that it's a timecode
                if('timecode' not in tx_rec_chans[0]):
                    raise ValueError(f'Expected timecode channel but got {row["channels"][0]}')
                
                #make sure that timecode types match
                if rx_tc_type != tx_rec_chans[0]:
                    raise ValueError(f'Tx timecode type is {tx_rec_chans[0]} but Rx timecode type is {rx_tc_type}')
                
                #one channel, only timecode
                tx_rec_tca=tx_rec_dat
                
                tx_extra_audio = None
                tx_extra_chans = None
            else:                
                #grab the same type of timecode we used for Rx
                tx_time_idx = tx_rec_chans.index(rx_tc_type)
                
                tx_rec_tca = tx_rec_dat[:,tx_time_idx]
                
                #extra channels
                tx_extra_audio = np.remove(tx_rec_dat,tx_time_idx,1)
                
                #copy to new array without timecode channel
                tx_extra_chans = tx_rec_chans.copy()
                del tx_extra_chans[tx_time_idx]
            
            #decode timecode
            tx_time, tx_snum = time_decode(rx_tc_type, tx_rec_tca, tx_rec_fs)

            #array for matching sample numbers
            tx_match_samples = []
            rx_match_samples = []


            for time,snum in zip(tx_time,tx_snum):
                
                #calculate diffrence from rx timecode
                time_diff = abs(rx_time - time)
                
                #find minimum diffrence
                min_v = np.amin(time_diff)

                #check that diffrence is small
                if min_v < timedelta(seconds=0.5):
                    
                    #get matching index
                    idx=np.argmin(time_diff)
                    
                    #append sample number
                    tx_match_samples.append(snum)
                    rx_match_samples.append(rx_snum[idx])

            #get matching frame start indicies
            mfr=np.column_stack((tx_match_samples, rx_match_samples))
            
            #get diffrence between matching timecodes
            mfd=np.diff(mfr, axis=0)

            
            #get ratio of samples between matches
            mfdr = mfd[:,0] / mfd[:,1] 

        
            if not np.all(np.logical_and(mfdr < (1+tc_warn_tol), mfdr>(1-tc_warn_tol))):
                warn(f'Timecodes out of tolerence for trial {trial+1}. {mfdr}')  
            
            #calculate first rx sample to use
            first=mfr[0,1]-mfr[0,0]
            
            #calculate last rx sample to use
            last=mfr[-1,1]+len(tx_rec_tca)-mfr[-1,0]+extra_samples - 1
            
            #get rx recording data from big array
            rx_rec=rx_dat[first:last+1,:]
            #remove timecode
            rx_rec = np.delete(rx_rec,rx_tc_idx,1)
            
            if(tx_extra_audio):
                #add in channels from Tx side
                rx_rec = np.append(rx_rec,tx_extra_audio,1)
            
            if tx_extra_chans:
                #add tx extra chans to rx extra chans
                out_chans=rx_extra_chans+tx_extra_chans
                out_audio=np.row_stack((rx_rec,tx_extra_audio))
            else:
                #no extra chans, all out chans from rx
                out_chans=rx_extra_chans
                out_audio=rx_rec
            
            #overwrite new channels to csv
            row['channels']=mcvqoe.base.audio_channels_to_string(out_chans)
            
            #TODO : process audio?
            
            # Create audiofile name/path for recording
            audioname = f'Rx{trial+1}_{row["Filename"]}.wav'
            audioname = os.path.join(wavdir, audioname)
            
            #save out Rx recording as given data type
            mcvqoe.base.audio_write(audioname,rx_fs,out_audio)
            
            #write row to new .csv
            writer.writerow(row)
        
        #copy Tx files into destination folder
        for name in glob.glob(os.path.join(tx_wav_path,'Tx_*')):
            #get clip name from path
            clip_name=os.path.basename(name)
            #construct destination name
            destname=os.path.join(wavdir,clip_name)
            #copy file
            shutil.copyfile(name,destname)



def main():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("tx_name",type=str)
    parser.add_argument("--extra-play", type=int, default=1)
    parser.add_argument("--rx-name", type=str, default=None)
    parser.add_argument("--outdir", type=str, default="")
    parser.add_argument("--audio-type", type=int, default=32)

    args = vars(parser.parse_args())

    twoloc_process(**args)

if __name__ == '__main__':
    main()