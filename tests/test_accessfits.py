# -*- coding: utf-8 -*-
"""
Created on Mon Nov 29 13:24:11 2021

@author: jkp4
"""
import os
import pkg_resources
import unittest

import numpy as np
import pandas as pd

import mcvqoe.accesstime as access

dirname = os.path.dirname(__file__)
class EvaluateTest(unittest.TestCase):
    ref_data_path = os.path.join(dirname, 'data', 'reference_data')
    data_path = os.path.join(dirname, 'data')
    
    sut_sesh_ids = {
            'analog_direct': 'capture_Analog_12-Nov-2020_08-26-11',
            'lte': 'capture_LTE_14-Apr-2021_16-11-22',
            'p25_direct': 'capture_P25Direct_17-Nov-2020_15-44-51',
            'p25_trunked_phase1': 'capture_P25-Phase1-Trunked_04-Nov-2020_07-21-19',
            'p25_trunked_phase2': 'capture_P25-Phase2-Vetted_29-Oct-2020_12-39-37',
            }
    
    def compare_fits_explicit(self, fit1, fit2, fit_description):
        for key in fit1.__dict__.keys():
            
            with self.subTest(fit_description=fit_description, fit_parameter=key):
                if key == 'I0':
                    # These should be identical
                    self.assertAlmostEqual(getattr(fit1, key), getattr(fit2, key))
                elif key != 'covar':
                    # Update what key to use to grab from covariance matrix
                    if key== 'lam':
                        covar_k = 'lambda'
                    else:
                        covar_k = key
                    # Grab variances for each parameter
                    var1 = fit1.covar.loc[covar_k, covar_k]
                    var2 = fit2.covar.loc[covar_k, covar_k]
                    # Uncertainty of the difference between the parameters is sqrt of the sum of variances
                    # We will use that as a delta for our check
                    total_unc = np.sqrt(var1 + var2)
                    self.assertAlmostEqual(getattr(fit1, key), getattr(fit2, key), delta=total_unc)
                    
    
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
            self.compare_fits_explicit(fit_data, ref_fit, fit_description='PTT Gate' + tw)
    
    def test_sut_access(self):
        
        ref_path = os.path.join(self.ref_data_path, 'reference-access-values.csv')
        sut_ref_data = pd.read_csv(ref_path)
        for tech, sesh_id in self.sut_sesh_ids.items():
            eval_obj = access.evaluate(sesh_id,
                                       test_path=self.data_path,
                                       test_type='COR',
                                       )
            sut_ref = sut_ref_data[sut_ref_data['Technology'] == tech]
            for ix, ref_row in sut_ref.iterrows():
                [access_time, ci] = eval_obj.eval(ref_row['alpha'])
                ref_ci = (ref_row['access_time'] 
                          + 1.96*ref_row['uncertainty'] * np.array([-1, 1]))
                with self.subTest(tech=tech, alpha=ref_row['alpha']):
                    self.assertTrue((ref_ci[0] <= ci[0] and ci[0] <= ref_ci[1])
                                    or (ci[0] <= ref_ci[0] and ref_ci[0] <= ci[1]))
    
    def test_sut_fits(self):
        
        ref_path = os.path.join(self.ref_data_path, 'reference-tech-fits.csv')
        sut_ref_data = pd.read_csv(ref_path, index_col=0)
        for tech, sesh_id in self.sut_sesh_ids.items():
            eval_obj = access.evaluate(sesh_id,
                                       test_path=self.data_path,
                                       test_type='COR',
                                       )
            ref = sut_ref_data.loc[tech]
            ref_fit = access.FitData(I0=ref['I0'],
                                     t0=ref['t0'],
                                     lam=ref['lambda'],
                                     covar=np.array(
                                         ((ref['t0_t0'], ref['t0_lambda']),
                                          (ref['lambda_t0'], ref['lambda_lambda']))
                                         ),
                                     )
            self.compare_fits_explicit(eval_obj.fit_data, ref_fit, fit_description=tech)
            
    def test_json_save_and_load(self):
        tech = 'lte'
        sesh_id = self.sut_sesh_ids[tech]
        eval_obj = access.evaluate(sesh_id,
                                   test_path=self.data_path,
                                   test_type='COR',
                                   )
        json_str = eval_obj.to_json()
        
        eval_json = access.evaluate(json_data=json_str)
        for alpha in np.arange(0.5, 1, 0.01):
            [a1, ci1] = eval_obj.eval(alpha)
            [a2, ci2] = eval_json.eval(alpha)
            with self.subTest(tech=tech, alpha=alpha):
                self.assertAlmostEqual(a1, a2, places=10)
                

class  AccessDataTest(unittest.TestCase):
    data_path = os.path.join(dirname, 'data', 'reference_data')
    ref_fname = 'ptt_ref_data.csv'
    ref_fpath = os.path.join(data_path, ref_fname)
    ptt_ref_data = pd.read_csv(ref_fpath)
    
    raw_data_path = os.path.join(dirname, 'data')
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
        data_path = self.raw_data_path
        
        # Test generic session ID with test_path
        x1 = access.AccessData(session_name, test_path=data_path)
        self.compare_access_df(x1.data, self.ptt_ref_data)
        
        # Test specific csv file names with test_path
        csv_path = os.path.join(data_path, 'csv')
        sesh_csvs = access.access_time_eval.find_session_csvs(session_name, csv_path)
        x2 = access.AccessData(test_names=sesh_csvs, test_path=data_path)
        self.compare_access_df(x2.data, self.ptt_ref_data)
        
        
        # Test specific csv file names with no test_path
        sesh_paths = [os.path.join(csv_path, x) for x in sesh_csvs]
        x3 = access.AccessData(test_names=sesh_paths)
        self.compare_access_df(x3.data, self.ptt_ref_data)
        
        # Test explicit wav paths
        test_wav_path = os.path.join(data_path, 'wav', session_name)
        x3w = access.AccessData(test_names=sesh_paths,
                            wav_dirs=len(sesh_paths) * [test_wav_path],
                            )
        self.compare_access_df(x3w.data, self.ptt_ref_data)


if __name__ == '__main__':
    
    unittest.main()

