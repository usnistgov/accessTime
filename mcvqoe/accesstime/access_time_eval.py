# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 14:26:30 2021

@author: wrm3
"""
# =============================================================================
# Import statements
# =============================================================================
import argparse
import json
import os
import pkg_resources
import re
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from scipy.optimize import curve_fit
from scipy.stats import norm
import mcvqoe.math

def find_session_csvs(session_id, data_path):
    data_csvs = os.listdir(data_path)
    
    sesh_search = re.compile(f'{session_id}_.+.csv')
    
    return list(filter(sesh_search.match, data_csvs))

def default_correction_data():
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
    
    cor_data = AccessData(sesh_csvs,
                          wav_dirs=[correction_csv_path] * len(sesh_csvs),
                          )
    return cor_data
    
# =============================================================================
# Class definitions
# =============================================================================
class AccessData():
    """

        Parameters
        ----------
        test_names : TYPE
            DESCRIPTION.
        test_path : TYPE, optional
            DESCRIPTION. The default is ''.
        wav_dirs : TYPE, optional
            DESCRIPTION. The default is [].
        use_reprocess : TYPE, optional
            DESCRIPTION. The default is True.
         : TYPE
            DESCRIPTION.
            
        Attributes
        ----------
        data : pd.DataFrame
            DESCRIPTION
        test_names : list
            DESCRIPTION
        test_info : dict
            DESCRIPTION
        cps : dict
            DESCRIPTION

        Returns
        -------
        None.

    """
    def __init__(self,
                 test_names,
                 test_path='',
                 wav_dirs=[],
                 use_reprocess=True,
                 ):
       
        self.use_reprocess = use_reprocess
        
        if isinstance(test_names, str):
            test_names = [test_names]
        if isinstance(wav_dirs, str):
            wav_dirs = [wav_dirs]

        if not wav_dirs:
            wav_dirs = (None, ) * len(test_names)
        
        # Initialize info arrays
        self.test_names = []
        self.test_info = dict()
        
        # Loop through all the tests and find files
        for tn, wd in zip(test_names, wav_dirs):
            # split name to get path and name
            # if it's just a name all goes into name
            dat_path, name = os.path.split(tn)
            # Split extension, ext is empty if none
            t_name, ext = os.path.splitext(name)
            
            # Check if a path was given to a .csv file
            if not dat_path and not ext == '.csv':
                # Generate using test_path
                dat_path = os.path.join(test_path, 'csv')
                # Find all csvs that match session id t_name
                dat_file = find_session_csvs(session_id=t_name,
                                              data_path=dat_path,
                                              )
                cp_path = os.path.join(test_path, 'wav')
            else:
                
                if test_path == '':
                    # Assume full path given
                    dat_file = [tn]
                    cp_path = os.path.join(os.path.dirname(dat_path), 'wav')
                    dat_path = ''
                    
                else:
                    # Assume we are supposed to use test path too
                    dat_file = [os.path.join(test_path, 'csv', tn)]
                    cp_path = os.path.join(test_path, os.path.dirname(dat_path), 'wav')
                    
            
            # Check if we were given an explicit wav directory
            if wd:
                # Use given path
                cp_path = wd
                # get test name from wav path
                
            else:
                # Otherwise get path to the wav dir
                
                # Remove possible R in t_name
                wt_name = t_name.replace('Rcapture', 'capture')
                
                sesh_search_str = re.compile('(capture_.+_\d{2}-\w{3}-\d{4}_\d{2}-\d{2}-\d{2})')
                sesh_search = sesh_search_str.search(wt_name)
                sesh_id = sesh_search.groups()[0]
                cp_path = os.path.join(cp_path, sesh_id)
            
            self.test_info[t_name] = {'data_path': dat_path,
                                     'data_file': dat_file,
                                     'cp_path': cp_path}
            self.test_names.append(t_name)
        self.data, self.cps = self.load_sessions()
            
    def load_sessions(self):
        """
        Load access time sessions and associated cutpoints files

        Returns
        -------
        tests : TYPE
            DESCRIPTION.
        tests_cp : TYPE
            DESCRIPTION.

        """
        
        tests = []
        tests_cp = {}
        for session, sesh_info in self.test_info.items():
            tests_cp[session] = {}
            for word_csv in sesh_info['data_file']:
                fname = os.path.join(sesh_info['data_path'], word_csv)
                if self.use_reprocess:
                    # Look for reprocessed file if it exists
                    fname = self.check_reprocess(fname)
                
                test = pd.read_csv(fname, skiprows=3)
                
                # Store test name as column in test
                sesh_search_str = re.compile('(capture_.+_\d{2}-\w{3}-\d{4}_\d{2}-\d{2}-\d{2})')
                sesh_search = sesh_search_str.search(session)
                sesh_id = sesh_search.groups()[0]
                test['name'] = sesh_id
                
                # Extract talker word combo from file name
                tw_search_str = r'([FM]\d)(_b\d{1,2}_w\d_)(\w+)(?:.csv)'
                tw_search_var = re.compile(tw_search_str)
                tw_search = tw_search_var.search(word_csv)
                if tw_search is None:
                    raise RuntimeError(f'Unable to determine talker word from filename {word_csv}')
                talker, bw_index, word = tw_search.groups()
                talker_word = talker + ' ' +  word
                # Store as column
                test['talker_word'] = talker_word
                
                
                # Load cutpoints, store in dict
                cp_name = 'Tx_' + talker + bw_index + word + '.csv'
                cp_path = os.path.join(sesh_info['cp_path'], cp_name)
                
                tests_cp[session][talker_word] = pd.read_csv(cp_path)
                
                
                with open(fname) as head_file:
                    audio_files = head_file.readline()
                    sample_rate = head_file.readline()
                
                fs_search_var = re.compile(r'\d+')
                fs_search = fs_search_var.search(sample_rate)
                if fs_search is not None:
                    fs = int(fs_search.group())
                else:
                    raise RuntimeError(f'No valid sample rate found in session header\n{fname}')
                
                # Determine length of T from cutpoints
                T = tests_cp[session][talker_word].loc[0]['End']/fs
                
                # Store PTT time relative to start of P1 
                test['time_to_P1'] = T - test['PTT_time']
                tests.append(test)
        tests = pd.concat(tests, ignore_index=True)
        
        return tests, tests_cp
    
    def check_reprocess(self, fname):
        """
        Look for a reprocessed data file in same path as fname.

        Searches for a reprocessed data file in same path as fname.
        Reprocessed data always starts as 'Rcapture', where original data
        starts with 'capture'. Returns reprocessed file name if it exists,
        otherwise returns original file name.

        Parameters
        ----------
        fname : str
            Path to a session csv file.

        Returns
        -------
        str:
            Path to reprocessed file if it exits, otherwise returns fname

        """
        dat_path, name = os.path.split(fname)
        if 'Rcapture' not in name:
            reprocess_fname = os.path.join(dat_path, 'R{}'.format(name))
            if os.path.exists(reprocess_fname):
                out_name = reprocess_fname
            else:
                out_name = fname
        else:
            out_name = fname

        return out_name

    def __str__(self):
        s = f'AccessData object, talker word combos: {np.unique(self.data.talker_word)}'
        return s
    
    

class FitData:

    def __init__(self, I0, t0, lam, covar, 
                 # curve_dat,
                 ):
        self.I0 = I0
        self.t0 = t0
        self.lam = lam
        self.covar = pd.DataFrame(covar,
                                  columns=['t0', 'lambda'],
                                  index=['t0', 'lambda'],
                                  )
    def __repr__(self):
        out = f'''Model:
    I0/(1 + exp((t-t0)/lambda))
    I0: {self.I0}
    lambda: {self.lam}
    t0: {self.t0}\n'''
        return out
    

class evaluate:
    """
    Parameters
    ----------
    test_names : str or list
        Name of test, or list of names of tests.

    test_path : str
        Path where test data is stored. Does not need to be passed if
        test_names contains full paths to files and wav_dirs is set as
        well.

    wav_dirs : str or list
        Paths to directories containing audio for a PSuD test. Must contain
        cutpoints for audio clips in data files.

    test_type : str
        DESCRIPTION.
    ptt_session_names : TYPE, optional
        DESCRIPTION. The default is None.
    **kwargs : TYPE
        DESCRIPTION.

    Returns
    -------
    None.
    """

    def __init__(self,
                 test_names=None,
                 test_path='',
                 wav_dirs=[],
                 use_reprocess=True,
                 test_type="COR",
                 correction_data=None,
                 json_data=None,
                 **kwargs):
        
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise TypeError(f'{k} is not a valid keyword argument')
        if json_data is not None:
            self.test_names, self.test_info, self.data, self.cps = evaluate.load_json_data(json_data)
        else:
            # Data loaded in
            data = AccessData(test_names=test_names,
                                   test_path=test_path,
                                   wav_dirs=wav_dirs,
                                   use_reprocess=use_reprocess,
                                   )
            self.data = data.data
            self.test_names = data.test_names
            self.test_info = data.test_info
            self.cps = data.cps
        
        # Assign correction data if it is given and relevant
        if correction_data is None and test_type == 'COR':
            self.cor_data = default_correction_data()
        elif test_type == 'COR':
            self.cor_data = correction_data
        else:
            self.cor_data = None
        # Determine if correction data matches input data, if not, raise an error
        if self.cor_data is not None:
            cor_tw = np.unique(self.cor_data.data['talker_word'])
            for tw in self.talker_words:
                if tw not in cor_tw:
                    raise ValueError(f'Missing talker word \'{tw}\'in correction data')
        
        self.fit_type = test_type
        self.fit_data = self.fit_curve_data(self.fit_type)
        
    @property
    def talker_words(self):
        return np.unique(self.data['talker_word'])

    def fit_curve_data(self, fit_type, talker_words=None):
        
        if talker_words is None:
            talker_words = self.talker_words

        valid_fit_types = ["COR", "LEG", "SUT"]
        # Initial parameters: naive guess
        init = [0, -0.1]
        # Define logistic function to fit to
        def logistic_fit(xdata, t0, lam):
                    return I0/(1+np.exp((xdata - t0)/lam))
            
        if fit_type == "LEG":
            # Calculate asymptotic intelligibility
            I0 = np.mean(self.data['P2_Int'])
            
            
            fit_data = curve_fit(logistic_fit,
                                 self.data['time_to_P1'],
                                 self.data['P1_Int'],
                                 p0=init,
                                 )
            fit_data = FitData(I0=I0,
                               t0=fit_data[0][0],
                               lam=fit_data[0][1],
                               covar=fit_data[1],
                               )
        elif fit_type in ["COR", "NoCOR"]:
            # Explicitly grab correction data
            cor_data = self.cor_data.data
            
            # Initialize dictionary to store corrected parameters
            cor_params = {
                'I0': 0,
                't0': 0,
                'lam': 0,
                'covar': np.array(([0, 0], [0,0]), dtype=np.dtype('float64')),
                }
            
            for tw in talker_words:
                # Get word data for given talker word combo
                cor_word_data = cor_data[cor_data['talker_word'] == tw]
                
                # Determine I0 for correction data (should alwyas be 1, so we don't track it after this)
                I0 = np.mean(cor_word_data['P2_Int'])
                if fit_type == "COR":
                    # Get correction fit
                    cor_fit = curve_fit(
                        logistic_fit,
                        cor_word_data['time_to_P1'],
                        cor_word_data['P1_Int'],
                        p0=init,
                        )
                else:
                    cor_fit = (
                        (0, 0),
                        ((0, 0), (0, 0))
                        )
                                 
                
                # Get word data for given talker word combo for SUT
                sut_word_data = self.data[self.data['talker_word'] == tw]
                # Determine I0 
                I0 = np.mean(sut_word_data['P2_Int'])
                # Get curve fit for SUT word
                sut_fit = curve_fit(
                    logistic_fit,
                    sut_word_data['time_to_P1'],
                    sut_word_data['P1_Int'],
                    p0=init,
                    )
                
                # Corrected t0 paramerter
                t0 = sut_fit[0][0] - cor_fit[0][0]
                # Add to corrected parameters dictionary
                cor_params['t0'] += t0
                
                # Corrected lambda
                lam = sut_fit[0][1] - cor_fit[0][1]
                # Add to corrected parameters dictoinary
                cor_params['lam'] += lam
                
                # Add SUT I0 to corrected parameters list
                cor_params['I0'] += I0
                
                # Get corrected variance and covariance of parameters
                var_t0 = sut_fit[1][0][0] + cor_fit[1][0][0]
                var_lam = sut_fit[1][1][1] + cor_fit[1][1][1]
                covar_lam_t0 = sut_fit[1][0][1] + cor_fit[1][0][1]
                
                # Store as np array
                cvar = np.array(([var_t0, covar_lam_t0],
                                 [covar_lam_t0, var_lam]))
                
                # Add into corrected parameters list
                cor_params['covar'] += cvar
                
            # Get number of talker word combinations
            N_words = len(talker_words)
            
            # Updated sums to be averages
            cor_params['I0'] = cor_params['I0']/N_words
            cor_params['t0'] = cor_params['t0']/N_words
            cor_params['lam'] = cor_params['lam']/N_words
            
            fit_data = FitData(
                I0=cor_params['I0'],
                t0=cor_params['t0'],
                lam=cor_params['lam'],
                covar=cor_params['covar'],
                )
            
            
        elif fit_type == "SUT":
            talker_word_combos = np.unique(self.data['talker_word'])
            fit_data = dict()
            for tw in talker_word_combos:
                data = self.data[self.data['talker_word'] == tw]
                I0 = np.mean(data['P2_Int'])
                
                word_fit = curve_fit(
                    logistic_fit,
                    data['time_to_P1'],
                    data['P1_Int'],
                    p0=init,
                    )
                fit_data[tw] = FitData(I0=I0,
                       t0=word_fit[0][0],
                       lam=word_fit[0][1],
                       covar=word_fit[1],
                       )
        else:
            raise ValueError(f"Fit type not one of: {valid_fit_types}")
        
        return fit_data
        

    def eval(self, alpha, fit_data=None, raw_intell=False, sys_dly_unc=0.07e-3/1.96,
             p=0.95):
        """
        Evaluate access delay for a given value of alpha.

        Parameters
        ----------
        alpha : TYPE
            DESCRIPTION.
        raw_intell : TYPE, optional
            DESCRIPTION. The default is False.
        sys_dly_unc : TYPE, optional
            DESCRIPTION. The default is 0.07e-3/1.96.
        p : TYPE, optional
            DESCRIPTION. The default is 0.95.

        Returns
        -------
        access : TYPE
            DESCRIPTION.
        ci : TYPE
            DESCRIPTION.

        """
        if fit_data is None:
            fit_data = self.fit_data
        
        if raw_intell:
            if alpha > fit_data.I0:
                raise ValueError(f'Invalid intelligibility level, must be <= {fit_data.I0}')
            # Rescale such that alpha is the fractoin of asymptotic
            alpha = alpha/fit_data.I0
        else:
            if alpha >= 1:
                raise ValueError('Invalid alpha level, must be less than 1')

        
        C = np.log((1-alpha)/alpha)
        access = fit_data.lam * C + fit_data.t0
        
        var_t = (
            np.power(C, 2) * fit_data.covar.loc["lambda", "lambda"]
            + fit_data.covar.loc["t0", "t0"] 
            + 2*C*fit_data.covar.loc["t0", "lambda"]
        )
        
        unc = np.sqrt(var_t + np.power(sys_dly_unc, 2))
        k = norm.ppf(1-(1-p)/2)
        ci = np.array([access - k*unc, access + k*unc]) 
        
        return access, ci
    
    def eval_intell(self, ptt_times=None, fit_data=None):
        
        if fit_data is None:
            fit_data = self.fit_data
        if ptt_times is None:
            ptt_times = np.arange(-0.6, 2.5, 0.02)
        
        intell = fit_data.I0/(1+np.exp((ptt_times - fit_data.t0)/fit_data.lam))
        
        return intell
    
    def to_json(self, filename=None):
        """
        Create json representation of access data

        Parameters
        ----------
        filename : str, optional
            If given save to json file. Otherwise returns json string. The default is None.

        Returns
        -------
        None.

        """
        cps = {}
        for sesh, sesh_cps in self.cps.items():
            cps[sesh] = {}
            for talker_word, cp in sesh_cps.items():
                cps[sesh][talker_word] = cp.to_json()
        # cps = {}
        # for talker_word, cp in self.cps.items():
        #     cps[talker_word] = cp.to_json()
        
        out_json = {
            'measurement': self.data.to_json(),
            'cps': cps,
            # 'test_info': json.dumps(self.test_info)
            'test_info': self.test_info,
                }
        
        # Final json representation of all data
        final_json = json.dumps(out_json)
        if filename is not None:
            with open(filename, 'w') as f:
                json.dump(out_json, f)
        
        return final_json
    
    @staticmethod
    def load_json_data(json_data):
        """
        Do all data loading from input json_data

        Parameters
        ----------
        json_data : TYPE
            DESCRIPTION.

        Returns
        -------
        test_names : list
            DESCRIPTION.
        test_info : dict
            DESCRIPTION.
        data : pd.DataFrame
            DESCRIPTION.
        cps : dict
            DESCRIPTION.

        """
        # TODO: Should handle correction data too!
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        # Extract data, cps, and test_info from json_data
        data = pd.read_json(json_data['measurement'])
        
        cps = {}
        cp_data = json_data['cps']
        for sesh, sesh_cps in cp_data.items():
            cps[sesh] = {}
            for talker_word, cp in sesh_cps.items():
                cps[sesh][talker_word] = pd.read_json(cp)
        
        # cps = {}
        # for talker_word, cp in json_data['cps'].items():
        #     cps[talker_word] = pd.read_json(cp)
        
        test_info = json_data['test_info']
        
        # Return normal Access data attributes from these
        return test_info.keys(), test_info, data, cps
    
    def plot(self, raw_intell=False, talkers=None, fit_type="COR",
             title='Access delay'):
        """
        Plot access delay curve with uncertainty

        Parameters
        ----------
        raw_intell : TYPE, optional
            DESCRIPTION. The default is False.
        talkers : TYPE, optional
            DESCRIPTION. The default is None.
        title : TYPE, optional
            DESCRIPTION. The default is 'Access delay'.

        Returns
        -------
        fig : TYPE
            DESCRIPTION.

        """
        # Valid range of alpha values to consider
        alphas = np.arange(0.5, 1, 0.01)
        
        # Determine if raw intelligibility or alpha values for x-axis
        if raw_intell:
            alphas = self.fit_data.I0 * alphas
            xlabel = 'Intelligibility'
        else:
            xlabel = 'alpha'
        
        
        if talkers is None:
            # Default is to use all talkers
            fit_data = self.fit_curve_data(fit_type)
        else:
            # Otherwise get corrected curve data for a subset determined by talkers
            fit_data = self.fit_curve_data(fit_type=fit_type,
                                           talker_words=talkers,
                                           )
        # Initialize dict for storing access info
        access = {
            'alpha': [],
            'access': [],
            'ci_l': [],
            'ci_u': [],
                  }
        
        for alpha in alphas:
            # Get access estimate and confidence interval
            a, ci = self.eval(alpha, raw_intell=raw_intell, fit_data=fit_data)
            access['alpha'].append(alpha)
            access['access'].append(a)
            access['ci_l'].append(ci[0])
            access['ci_u'].append(ci[1])
        # Make data frame of all access info
        df = pd.DataFrame(access)
        
        # Initialize figure
        fig = go.Figure()
        
        # Plot access estimate
        fig.add_trace(
            go.Scatter(
                x=df['alpha'],
                y=df['access'],
                legendgroup='Ah',
                legendgrouptitle_text='Access delay',
                name='estimate',
                )
            )
        
        # Plot access confidence interval lower bound
        fig.add_trace(
            go.Scatter(
                x=df['alpha'],
                y=df['ci_l'],
                line={'color': 'blue',
                      'dash': 'dash'},
                legendgroup='Ah',
                name='95% confidence interval',
                )
            )
        # Plot access confidence interval upper bound
        fig.add_trace(
            go.Scatter(
                x=df['alpha'],
                y=df['ci_u'],
                line={'color': 'blue',
                      'dash': 'dash'},
                legendgroup='Ah',
                name='95% confidence interval',
                showlegend=False,
                )
            )
        # Add title and axis labels
        fig.update_layout(            
            title=title,
            xaxis_title=xlabel,
            yaxis_title='Access time [seconds]',
        )
        return fig
    
    def plot_intell(self, show_raw=True, talkers=None, fit_type="COR",
                    title='Intelligibility Curves'):
        """
        Plot intelligibility curves

        Parameters
        ----------
        show_raw : TYPE, optional
            DESCRIPTION. The default is True.
        talkers : TYPE, optional
            DESCRIPTION. The default is None.
        title : TYPE, optional
            DESCRIPTION. The default is 'Intelligibility Curves'.

        Raises
        ------
        ValueError
            DESCRIPTION.

        Returns
        -------
        fig : TYPE
            DESCRIPTION.

        """
        # Get individual fits for each talker word combo
        tw_fits = self.fit_curve_data("SUT")
        
        
        if talkers is None:
            # Default is use all talkers
            talkers = list(tw_fits.keys())
        else:
            if isinstance(talkers, str):
                talkers = [talkers]
            # Ensure that talkers passed are valid
            valid_talkers = tw_fits.keys()
            for talker in talkers:
                if talker not in valid_talkers:
                    raise ValueError(f'Invalid talker \'{talker}\'. talkers must be subset of {valid_talkers}')
        
        # Initialize figure
        fig = go.Figure()
        # TODO: Come up with better ptt_times?
        ptt_times = np.arange(-0.6, 2.5, 0.02)
        
        # Get default plotly colors
        colors = px.colors.qualitative.Plotly
        # Initizialize index tracker for which color to use
        color_ix = 0
        
        if len(talkers) > 1:
            talkers.append(tuple(talkers))
        for talker in talkers:
            if isinstance(talker, tuple):
                talker_fit = self.fit_curve_data(fit_type, talker_words=talker)
                talkergroup = fit_type + ': ' + ', '.join(talker)
            else:
                # Get fit data for talker word combo
                talker_fit = tw_fits[talker]
                talkergroup = talker
            
            # Evaluate intelligibility for talker word combo
            talker_intell = self.eval_intell(ptt_times=ptt_times, fit_data=talker_fit)
            
            # Set color
            color = colors[color_ix]
            
            # Plot intelligibility curve
            fig.add_trace(
                go.Scatter(
                    x=ptt_times,
                    y=talker_intell,
                    line={
                        'width': 6,
                        'color': color,
                        },
                    legendgrouptitle_text=talkergroup,
                    legendgroup=talkergroup,
                    name= 'intelligibility curve',
                    )
                )
            if show_raw == True and isinstance(talker, str):
                # Get raw data for talker word combo
                talker_data = self.data[self.data['talker_word'] == talker]
                nrow, _ = talker_data.shape
                # Plot raw P1 intelligibility data
                fig.add_trace(
                    go.Scatter(
                        x=talker_data['time_to_P1'],
                        y=talker_data['P1_Int'],
                        hovertext=np.array([f'Trial: {i}' for i in np.arange(1, nrow+1)]),
                        line={
                            'color': color,
                            },
                        legendgroup=talkergroup,
                        mode='markers',
                        name='raw data'
                        )
                    )
            # Iterate color
            if color_ix == len(colors) - 1:
                color_ix = 0
            else:
                color_ix += 1
        # Add title, axes labels
        fig.update_layout(            
            title=title,
            xaxis_title='Time from PTT to P1 [seconds]',
            yaxis_title='Intelligibility',
        )
        
        return fig


# =============================================================================
# Main definition
# =============================================================================
def main():
    """
    Evalaute Access Time data with command line arguments.

    Returns
    -------
    None.

    """
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description=__doc__)
    parser.add_argument('test_names',
                        type=str,
                        nargs="+",
                        action="extend",
                        help=("Test names (same as name of folder for wav"
                              "files)"))
    parser.add_argument('-p', '--test-path',
                        default='',
                        type=str,
                        help=("Path where test data is stored. Must contain"
                              "wav and csv directories."))

    parser.add_argument('-a', '--alpha',
                        default=[],
                        nargs="+",
                        action="extend",
                        type=float,
                        help="Values to evalaute access at. Either relative to asymptotic intelligibility or raw intelligibility values (see --relative-intell)")

    parser.add_argument('-n', '--no-reprocess',
                        default=True,
                        action="store_false",
                        help="Do not use reprocessed data if it exists.")
    
    parser.add_argument('-r', '--raw-intell',
                        default=True,
                        action="store_false",
                        help="Evaluate access with alpha as raw intelligibility.")
    

    args = parser.parse_args()

    eval_obj = evaluate(args.test_names,
                      test_path=args.test_path,
                      use_reprocess=args.no_reprocess)
    
    print("Results shown as Access(alpha) = mean, (95% C.I.)")
    msg_str = "Access({:.4f}) = {:.4f} s, ({:.4f},{:.4f}) s"
    for alpha in args.alpha:
        atime, ci = eval_obj.eval(alpha,
                                  raw_intell=args.raw_intell,
                                  )
        print(msg_str.format(alpha,
                             atime,
                             ci[0],
                             ci[1],
                             ))

# =============================================================================
# Execute if run as main script
# =============================================================================
if __name__ == "__main__":
    main()
