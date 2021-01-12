# -*- coding: utf-8 -*-
"""
Created on Tue Jan 12 08:43:22 2021

@author: jkp4
"""
import pdb
import numpy as np
def bootstrap_ci(x,p=0.95,R=1e4,stat=np.mean):
    """
    Bootstrap confidence interval for array of data
    

    Parameters
    ----------
    x : np.ndarray
        Data for which to calculate a confidence interval for stat.
    p : float, optional
        Confidence level of output interval. The default is 0.95.
    R : int, optional
        Number of resamples to calculate. The default is 1e4.
    stat : function, optional
        Statistic for confidence interval. The default is np.mean.

    Returns
    -------
    ci : np.ndarray
         Confidence interval of data for stat
         
    resamples : list
         Values of stat for each resample

    """
    # Force R to be an int
    if(type(R) is not int):
        R = int(R)
    # Length of data
    N = len(x)
    # Array to store resample stat values in 
    resamples = []
    # Random generator
    gen = np.random.default_rng()
    
    for k in range(R):
       # Get resample of same size as x (with replacement)
       resamp = gen.choice(x,N)
       # Store statisitc of resample
       resamples.append(stat(resamp))
   
    # Lower bound of confidence interval
    q_l = (1-p)/2
    # Upper bound of confidence interval
    q_u = 1 - q_l
    # Confidence interval
    ci = np.quantile(resamples,[q_l,q_u])
    return((ci,resamples))        

def standard_error(x):
    """
    Calculate standard error for data in x.
    
    This method assumes normality conditions are reasonable.

    Parameters
    ----------
    x : np.ndarray
        Data.

    Returns
    -------
    se : float
        Standard error of x

    """
    se = np.std(x)/np.sqrt(len(x))
    return(se)

def compare_uncs(x):
    """
    Calculate standard error and bootstrap based confidence intervals
    
    A nice sanity check that in well behaved circumstances, standard error is equivalent to bootstrap confidence interval results. Computes 95% confidence interval.

    Parameters
    ----------
    x : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    x_mean = np.mean(x)
    
    gum_u = standard_error(x)
    
    x_unc = 1.96*gum_u
    
    print("GUM Uncertainty (95% C.I.): x = {:.4f}, ({:.4f},{:.4f})".format(x_mean,x_mean-x_unc,x_mean+x_unc))
    
    b_u,_ = bootstrap_ci(x)
    print("Bootstrap Uncertainty (95% C.I.): x = {:.4f}, ({:.4f},{:.4f})".format(x_mean,b_u[0],b_u[1]))


    