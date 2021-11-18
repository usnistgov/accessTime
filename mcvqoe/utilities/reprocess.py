#!/usr/bin/env python

import argparse
import csv
import importlib.resources
import mcvqoe
import os.path
import scipy.io.wavfile
import sys
import tempfile

#expected path components for csv files
csv_path_names = ('csv','data')

measurement_dir_modules = {
    'Access_Time' : 'mcvqoe.accesstime',
    'Intelligibility' : 'mcvqoe.intelligibility',
    'Mouth_2_Ear' : 'mcvqoe.mouth2ear',
    'PSuD' : 'mcvqoe.psud',
}

def make_parser():

    #-----------------------[Setup ArgumentParser object]-----------------------

    parser = argparse.ArgumentParser(
        description="Reprocess audio files and write a new .csv with newly measured values")
    parser.add_argument('datafile', default=None, type=str,
                        help='CSV file from test to reprocess')
    parser.add_argument('outfile', default=None, type=str, nargs='?',
                        help='file to write reprocessed CSV data to. Can be the same name as datafile to overwrite results. if omitted output will be written to stdout')
    parser.add_argument('-m', '--measurement', type=str, default=None, metavar='M',
                        help='measurement to use to do reprocessing')
    parser.add_argument('--audio-path', type=str, default=None, metavar='P', dest='audio_path',
                        help='Path to audio files for test. Will be found automatically if not given')
    parser.add_argument('-s', '--split-audio-folder', default='', type=str, dest='split_audio_dest',
                        help='Folder to store single word clips to')

    return parser

def get_module(module_name=None, datafile=None):

    if not module_name:
        #no name given, see if we can find one

        #get absolute path to .csv file
        abs_csv_path = os.path.abspath(datafile)

        #split once to remove filename
        path_extra, fname = os.path.split(abs_csv_path)

        for expected_name in csv_path_names:
            path_extra, fold = os.path.split(path_extra)

            if fold != expected_name:
                raise RuntimeError(f'Unexpected directory \'{fold}\', unable to determine measurement.')

        #get the name of the data directory
        measurement_dir = os.path.basename(path_extra)

        #get module name, will fail if incorrect
        module_name = measurement_dir_modules[measurement_dir]
    else:
        #name given, clean up and use

        #make lowercase
        module_name = module_name.lower()

        #check if full import path was given
        if module_name.startswith('mcvqoe.') :
            #add mcvqoe to the module include
            module_name = 'mcvqoe.' + module_name

    #load module and return
    return importlib.import_module(module_name).measure

def reprocess_file(test_obj, datafile, out_name, **kwargs):

        print(f'Loading test data from \'{datafile}\'', file=sys.stderr)
        #read in test data
        test_dat=test_obj.load_test_data(datafile, **kwargs)

        print(f'Reprocessing test data to \'{out_name}\'', file=sys.stderr)

        test_obj.post_process(test_dat, out_name, test_obj.audio_path)


def main():

    #-----------------------------[Parse arguments]-----------------------------

    #get parser
    parser = make_parser()

    args = parser.parse_args()

    #---------------------------[Load Measure Class]---------------------------

    measurement_class = get_module(module_name=args.measurement, datafile=args.datafile)

    #---------------------------[Create Test object]---------------------------

    #create test obj to reprocess with
    test_obj=measurement_class()


    test_obj.split_audio_dest = args.split_audio_dest


    with tempfile.TemporaryDirectory() as tmp_dir:

        if(args.outfile=='--'):
            #print results, don't save file
            out_name=os.path.join(tmp_dir,'tmp.csv')
            print_outf=True
        elif(args.outfile):
            out_name=args.outfile
            print_outf=False
        else:
            #split data file path into parts
            d,n=os.path.split(args.datafile)
            #construct new name for file
            out_name=os.path.join(d,'R'+n)
            print_outf=False

        reprocess_file(test_obj, args.datafile, out_name, audio_path=args.audio_path)

        if(print_outf):
            with open(out_name,'rt') as out_file:
                dat=out_file.read()
            print(dat)

        print(f'Reprocessing complete for \'{out_name}\'', file=sys.stderr)


#main function
if __name__ == "__main__":
    main()