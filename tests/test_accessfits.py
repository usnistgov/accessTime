# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 13:24:11 2021

@author: jkp4
"""
import itertools
import os
import pkg_resources
import re
import unittest

import numpy as np
import pandas as pd

import mcvqoe.accesstime as access


# def test_tech(session_name):
#     sesh_wav_path = os.path.join(wav_path, session_name)
#     sesh_csv_paths = []
#     csv_files = os.listdir(csv_path)
    
#     for csvfile in csv_files:
#         if session_name in csvfile:
#             csvpath = os.path.join(csv_path, csvfile)
#             sesh_csv_paths.append(csvpath)
    
#     for sesh_path in sesh_csv_paths:
#         sesh_file = os.path.basename(sesh_path)
#         search_str = r'()'
#     cut_files = os.listdir(sesh_wav_path)
#     sesh_cut_paths = []
#     for cut_file in cut_files:
#         if any([cut_file in x for x in sesh_csv_paths]):
#             sesh_cut_paths.append(cut_file)
        
#     print(f'cut_files: {sesh_cut_paths}\ncsv_files: {sesh_csv_paths}')
#     ah = access.AccessData(session_names=sesh_csv_paths,
#                       cut_names=sesh_cut_paths,
#                       session_dir='', cut_dir='')
#     import pdb; pdb.set_trace()

class EvaluateTest(unittest.TestCase):
    ref_data_path = ''
    
    def compare_fits_explicit(self, fit1, fit2):
        for key in fit1.__dict__.keys():
            if key == 'covar':
                f1_covar = getattr(fit1, key)
                f2_covar = getattr(fit2, key)
                covar_diff = np.abs(f1_covar - f2_covar)
                # TODO: Compare dataframes see:
                # https://stackoverflow.com/questions/38839402/how-to-use-assert-frame-equal-in-unittest
                print('TODO: I DIDNT COMPARE COVARIANCE YET')
            else:
                self.assertAlmostEqual(getattr(fit1, key), getattr(fit2, key))
    
    def test_ptt_fits(self):
        ptt_ref_data_fname = 'PTT-gate-word-fits.csv'
        ptt_ref_data_path = os.path.join(self.ref_data_path, ptt_ref_data_fname)
        
        ref_data = pd.read_csv(ptt_ref_data_path, index_col=0)
        correction_csv_path = pkg_resources.resource_filename(
            'mcvqoe.accesstime', 'correction_data'
            )
        correction_csvs = pkg_resources.resource_listdir(
            'mcvqoe.accesstime', 'correction_data'
            )
        
        sesh_csvs = []
        for ccsv in correction_csvs:
            if 'capture' in ccsv:
                sesh_csvs.append(os.path.join(correction_csv_path, ccsv))
        
        eval_obj = access.evaluate(sesh_csvs,
                                   wav_dirs=[correction_csv_path] * len(sesh_csvs),
                                   test_type='SUT'
                                   )
        for tw, fit_data in eval_obj.fit_data.items():
            
            ref = ref_data.loc[tw]
            ref_fit = access.FitData(I0=ref['I0'],
                                     t0=ref['t0'],
                                     lam=ref['lambda'],
                                     covar=np.array(
                                         ((ref['t0_t0'], ref['t0_lambda']),
                                          (ref['lambda_t0'], ref['lambda_lambda']))
                                         ),
                                     )
            self.compare_fits_explicit(fit_data, ref_fit)
            

class  AccessDataTest(unittest.TestCase):
    ptt_ref_data = pd.read_csv('ptt_ref_data.csv')
    tol = 1e-16
    def compare_access_df(self, df1, df2):
        nrow, _ = df1.shape
        if nrow != df2.shape[0]:
            raise ValueError('Dataframes have different number of rows')
        
        data_check = np.sum(df1 == df2)
        data_check['time_to_P1'] = np.sum(np.abs(df1['time_to_P1'] - df2['time_to_P1']) < self.tol)
        passes = []
        for col, match in data_check.items():
            if col != 'TimeGap':
                tpass = match == nrow
                passes.append(tpass)
        
        self.assertEqual(np.sum(passes), len(df1.columns) - 1)
    
    def test_init(self):
        
        session_name = 'capture_PTT-gate_14-May-2021_07-30-20'
        data_path = os.path.join('..', 'accessTime', 'inst', 'extdata')
        
        # Test generic session ID with test_path
        x1 = access.AccessData(session_name, test_path=data_path)
        self.compare_access_df(x1.data, self.ptt_ref_data)
        
        # Test specific csv file names with test_path
        csv_path = os.path.join(data_path, 'csv')
        sesh_csvs = access.access_time_eval.find_session_csvs(ptt_session, csv_path)
        x2 = access.AccessData(test_names=sesh_csvs, test_path=data_path)
        self.compare_access_df(x2.data, self.ptt_ref_data)
        
        
        # Test specific csv file names with no test_path
        sesh_paths = [os.path.join(csv_path, x) for x in sesh_csvs]
        x3 = access.AccessData(test_names=sesh_paths)
        self.compare_access_df(x3.data, self.ptt_ref_data)
        
        # Test explicit wav paths
        x3w = access.AccessData(test_names=sesh_paths,
                            wav_dirs=len(sesh_paths) * [test_wav_path],
                            )
        self.compare_access_df(x3w.data, self.ptt_ref_data)

def test_init(session_name, data_path):
    ptt_session = session_name
    
    data_objs = []
    
     # Test generic session ID with test_path
    x1 = access.AccessData(ptt_session, test_path=data_path)
    data_objs.append(x1)
    
    # Test specific csv file names with test_path
    sesh_csvs = access.access_time_eval.find_session_csvs(ptt_session, csv_path)
    x2 = access.AccessData(test_names=sesh_csvs, test_path=data_path)
    data_objs.append(x2)
    
    # TODO:
    # Test specific csv file names with no test_path
    sesh_paths = [os.path.join(csv_path, x) for x in sesh_csvs]
    x3 = access.AccessData(test_names=sesh_paths)
    data_objs.append(x3)
    # Can you do non-specific wav paths with specific csv paths?
    
    # TODO: None of these test wav_path separately...
    # Test explicit wav paths
    test_wav_path = os.path.join(wav_path, ptt_session)
    cp_names = os.listdir(test_wav_path)
    
    # x1w = access.AccessData(ptt_session, test_path=data_path, wav_dirs=cp_paths)
    # x2w = access.AccessData(test_names=sesh_csvs, test_path=data_path, wav_dirs=cp_paths)
    x3w = access.AccessData(test_names=sesh_paths,
                            wav_dirs=len(sesh_paths) * [test_wav_path],
                            )
    data_objs.append(x3w)
    
    for obj1, obj2 in itertools.combinations(data_objs, 2):
        data_check = np.sum(obj1.data == obj2.data)
        nrow, _ = obj1.data.shape
        for col, match in data_check.items():
            if col != 'TimeGap':
                tpass = match == nrow
                if not tpass:
                    raise RuntimeError(f'init mismatch in data:\n{obj1};\n{obj2}')


if __name__ == '__main__':
    
    data_path = os.path.join('..', 'accessTime', 'inst', 'extdata')
    csv_path = os.path.join(data_path, 'csv')
    wav_path = os.path.join(data_path, 'wav')
    
    ptt_session = 'capture_PTT-gate_14-May-2021_07-30-20'
    # test_tech(ptt_session)
    
    # Test generic session ID with test_path
    x1 = access.AccessData(ptt_session, test_path=data_path)
    
    # Test specific csv file names with test_path
    sesh_csvs = access.access_time_eval.find_session_csvs(ptt_session, csv_path)
    x2 = access.AccessData(test_names=sesh_csvs, test_path=data_path)
    
    # TODO:
    # Test specific csv file names with no test_path
    sesh_paths = [os.path.join(csv_path, x) for x in sesh_csvs]
    x3 = access.AccessData(test_names=sesh_paths)
    # Can you do non-specific wav paths with specific csv paths?
    
    # TODO: None of these test wav_path separately...
    # Test explicit wav paths
    test_wav_path = os.path.join(wav_path, ptt_session)
    cp_names = os.listdir(test_wav_path)
    cp_paths = [os.path.join(test_wav_path, x) for x in cp_names]
    
    # x1w = access.AccessData(ptt_session, test_path=data_path, wav_dirs=cp_paths)
    # x2w = access.AccessData(test_names=sesh_csvs, test_path=data_path, wav_dirs=cp_paths)
    x3w = access.AccessData(test_names=sesh_paths,
                            wav_dirs=len(sesh_paths) * [test_wav_path],
                            )
    
    test_init(ptt_session, data_path)
    unittest.main()

