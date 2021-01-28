def approx_permutation_test(success, ts_ix):
    """
    Parameters
    ----------
    success : NumPy Array
        Array of MRT success values for all trials for the current clip
    ts_ix : NumPy Array
        Indices of trials from latest timestep
        
    Return
    ------
    Boolean
        Bool value of pval >= alpha
        
    """
    
    # p-value threshold: Threshold for accepting observed value or not.
    # The higher alpha is, the "stricter" our stopping criteria is.
    alpha = 0.05
    
    # Isolate scores for p1 and p2 (first and second play of the word)
    ## p1 only care about success results from trials at last timestep
    p1_success = success[0, ts_ix]
    ## p2 care about all trials so far for given clip
    p2_success = success[1, :]
    
    # Observed statistic
    observed = np.mean(p2_success) - np.mean(p1_success)
    
    # Number of trials in population 1
    m = len(p1_success)
    # Number of trials in population 2
    k = len(p2_success)
    
    # Total number of trials between populations
    n = m+k
    combo = [p1_success, p2_success]
    # Number of resamples to perform
    R = 10000
    # Initialize difference array
    diffs = np.zeros((R, 1))
    
    for k in range(len(R)):
        # Create random permutation for resampling
        permIx = np.random.permutation(n)
        # Grab first m elements of random order for population 1
        p1 = combo[permIx[0:m]]
        # Grab remaining K elements of random order for population 2
        p2 = combo[permIx[(m+1):]]
        
        # Compute resample statistic (difference of means)
        diffs[k] = np.mean(p2) - np.mean(p1)
    
    # Calculate p-value for likelihood that observed came from mixed
    # distribution
    pval_sum = diffs >= observed
    pval = (np.count_nonzero(pval_sum))/R
    
    # If pval is greater than alpha
    if (pval >= alpha):
        return True
    else:
        return False