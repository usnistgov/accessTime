# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 13:24:11 2021

@author: jkp4
"""
import os
import re
# import mcvqoe.accesstime as access
data_path = os.path.join('..', 'accessTime', 'inst', 'extdata')
csv_path = os.path.join(data_path, 'csv')
wav_path = os.path.join(data_path, 'wav')



def test_tech(session_name):
    sesh_wav_path = os.path.join(wav_path, session_name)
    sesh_csv_paths = []
    csv_files = os.listdir(csv_path)
    
    for csvfile in csv_files:
        if session_name in csvfile:
            csvpath = os.path.join(csv_path, csvfile)
            sesh_csv_paths.append(csvpath)
    
    for sesh_path in sesh_csv_paths:
        sesh_file = os.path.basename(sesh_path)
        search_str = r'()'
    cut_files = os.listdir(sesh_wav_path)
    sesh_cut_paths = []
    for cut_file in cut_files:
        if any([cut_file in x for x in sesh_csv_paths]):
            sesh_cut_paths.append(cut_file)
        
    print(f'cut_files: {sesh_cut_paths}\ncsv_files: {sesh_csv_paths}')
    # access.AccessData(session_names=sesh_csv_paths,
    #                   cut_names=sesh_cut_paths)

if __name__ == '__main__':
    ptt_session = 'capture_PTT-gate_14-May-2021_07-30-20'
    test_tech(ptt_session)

