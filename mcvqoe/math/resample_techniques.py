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

def approx_permutation_test(x, y,accept_threshold=0.05,R=1e4,stat=np.mean,tail='two'):
    """
    Perform an approximate permutation test to test if two sets of data are 
    from equivalent distributions.
    
    Null hypothesis in this test says that x is from the same distribution as 
    y
    
    Parameters
    ----------
    x : NumPy Array
        Array of data from first condition
    
    y : NumPy Array
        Array of data from second condition
        
    accept_threshold : float
        Value that p-value is compared to either reject or accept the Null 
        hypothesis. Default is 0.05.
        
    R : int
        Number of repetitions of resamples to perform. Default is 1e4
        
    stat : function
        Statistic to perform on data. Defaults to np.mean
        
    tail : str
        Determine if you do a one-sided or two-sided approximate permutation 
        test. Acceptable values are "left", "right", or "two". If tail is 
        "left", the test considers what fraction of resampled differences are 
        less than the observed statistic. If tail is "right", the test 
        considers what fraction of resampled differences are greater than the 
        observed statistic. If tail is "two", the test considers what fraction 
        of the absolute value of resampled differences are greater than the 
        absolute value of the observed statistic.
        
    
        
    Return
    ------
    Boolean
        Rejection or not that data comes from same distribution.
        
    """ 
    
    # Force R to be an int
    if(type(R) is not int):
        R = int(R)
    
    # Observed statistic
    observed = stat(x) - stat(y)
    
    # Number of trials in population 1
    m1 = len(x)
    # Number of trials in population 2
    m2 = len(y)
    
    # Total number of trials between populations
    n = m1 + m2
    # Combine both populations
    combo = np.concatenate((x,y))
    
    # Initialize difference array
    diffs = np.zeros((R, 1))
    
    # Random generator
    gen = np.random.default_rng()
    
    for k in range(R):
        # Create random permutation for resampling
        permIx = gen.permutation(n)
        
        # Grab first m elements of random order for population 1
        x_resamp = combo[permIx[0:m1]]
        # Grab remaining K elements of random order for population 2
        y_resamp = combo[permIx[m1:]]
        
        # Compute resample statistic (difference of means)
        diffs[k] = stat(x_resamp) - stat(y_resamp)
    
    # Calculate p-value for likelihood that observed came from mixed
    # distribution
    if(tail == 'left'):
        #Consider how many resamples were lower than observed value (how far left is our observation?)
        pval_sum = diffs <= observed
        
    elif(tail == 'right'):
        # Consider how many resamples were greater than observed value (how far right is our observation)
        pval_sum = diffs >= observed
    elif(tail == 'two'):
        # Consider how many resamples were larger in magnitude than observed value (how far from either tale is our observation)
        pval_sum = abs(diffs) >= abs(observed)
    else:
        raise ValueError('Unrecognized tail argument: {}. Must be either left, right, or two.'.format(tail))
    
    # Get fraction of resamples that achieved tail condtions
    pval = (np.count_nonzero(pval_sum))/R
    
    if(pval <= accept_threshold):
        # If pval is less than accept_threshold, reject Null hypothesis
        reject = True
    else:
        # If pval is greater than accept_threshold, do not reject Null hypothesis
        reject = False
    return(reject)

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


    