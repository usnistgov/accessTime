#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 29 11:12:57 2021

@author: jkp4
"""

import unittest
import mcvqoe.math
import numpy as np
import xmlrunner


class Test_Approx_Perm_Test(unittest.TestCase):
    
    # Number of tests to run
    N_tests = int(1e3)
    
    # Set tolerance for random tests to have some error
    random_tol = 2/np.sqrt(N_tests)
    
    def test_approx_permutation_two_tail(self):
        
        rejects = []
        
        # Define distribution for data
        mu = 0
        sigma = 1
        N = 100
        
        # Set reject threshold to 20%
        reject_threshold= 0.2
        for k in range(self.N_tests):
            # Draw from data
            x = np.random.normal(mu,sigma,N)
            y = np.random.normal(mu,sigma,N)
            
            # Test if data are from same distribution
            equiv = mcvqoe.math.approx_permutation_test(x, 
                                                        y,
                                                        accept_threshold=reject_threshold,
                                                        tail="two",
                                                        R = 1e3)
            rejects.append(equiv)
        # Fraction that were rejected
        reject_percent = np.sum(rejects)/len(rejects)
        
        self.assertLessEqual(abs(reject_threshold - reject_percent), self.random_tol)

    def test_approx_permutation_left_tail(self):
        
        rejects = []
        
        # Define distribution for data
        mu = 0
        sigma = 1
        N = 100
        
        # Set reject threshold to 20%
        reject_threshold= 0.2
        for k in range(self.N_tests):
            # Draw from data
            x = np.random.normal(mu,sigma,N)
            y = np.random.normal(mu,sigma,N)
            
            # Test if data are from same distribution
            equiv = mcvqoe.math.approx_permutation_test(x, 
                                                        y,
                                                        accept_threshold=reject_threshold,
                                                        tail="left",
                                                        R = 1e3)
            rejects.append(equiv)
        # Fraction that were rejected
        reject_percent = np.sum(rejects)/len(rejects)
        
        self.assertLessEqual(abs(reject_threshold - reject_percent), self.random_tol)

    def test_approx_permutation_right_tail(self):
        
        rejects = []
        
        # Define distribution for data
        mu = 0
        sigma = 1
        N = 100
        
        # Set reject threshold to 20%
        reject_threshold= 0.2
        for k in range(self.N_tests):
            # Draw from data
            x = np.random.normal(mu,sigma,N)
            y = np.random.normal(mu,sigma,N)
            
            # Test if data are from same distribution
            equiv = mcvqoe.math.approx_permutation_test(x, 
                                                        y,
                                                        accept_threshold=reject_threshold,
                                                        tail="right",
                                                        R = 1e3)
            rejects.append(equiv)
        # Fraction that were rejected
        reject_percent = np.sum(rejects)/len(rejects)
        
        self.assertLessEqual(abs(reject_threshold - reject_percent), self.random_tol)
        
class Test_Uncertainty(unittest.TestCase):
    
    # Number of tests to run
    N_tests = int(1e3)
    
    # Set tolerance for random tests to have some error
    random_tol = 2/np.sqrt(N_tests)
    
    def test_bootstrap_ci(self):
        
        contains_mean = []
    
        # Define distribution for data
        mu = 0
        sigma = 1
        N = 100
        
        # Set confidence level to 80%
        confidence_level = 0.8
        for k in range(self.N_tests):
            # Draw from data
            x = np.random.normal(mu,sigma,N)
            
            ci,_ = mcvqoe.math.bootstrap_ci(x,
                                            p=confidence_level,
                                            R=1e3)
            
            if(ci[0] <= mu and mu <= ci[1]):
                cm = True
                
            else:
                cm = False
            
            contains_mean.append(cm)
        
        # Fraction that were rejected
        contained_percent = np.mean(contains_mean)
        
        self.assertLessEqual(abs(confidence_level - contained_percent), self.random_tol)
        
    def test_standard_error(self):
        
        x = np.array([-0.75960479, -0.22052938, -0.96953799,  0.52929507,  0.97484278,
       -0.06694255, -0.11987828,  0.25715125,  0.17783594, -0.15757887,
       -0.75108778,  0.31470708,  0.77996851, -1.38874269,  0.72690251,
       -0.90424546, -0.21326391, -2.00467522, -0.78693889, -0.44446621,
        0.57539839, -0.34350244, -0.99507437,  0.99960533,  0.41552902,
        0.98838011, -0.48765714, -2.65290767,  0.72182913, -1.33695184,
        1.41531883, -1.37074593, -2.92162947,  1.4975616 , -2.67412797,
       -1.20711052,  0.61949463, -0.75253408,  0.29971613, -0.06008689,
        1.19634214,  1.49108975, -1.08290312, -1.24239805, -0.55013731,
       -0.70536895, -0.18239225, -0.49810937, -0.89152384, -0.88450113,
        0.3679832 , -0.2648769 ,  0.79951788, -2.50959125,  0.76784678,
        0.79743866,  0.79683056, -0.45257348,  0.52986986,  0.97417074,
        1.19670114,  1.58853588,  0.20471247,  0.32039648,  0.76310691,
       -0.92878694, -0.89100717, -0.49737375,  0.85576116,  0.10520707,
        0.66210508, -1.11311455,  1.60129306,  0.51927147,  0.93705721,
        0.3880829 ,  0.36928311, -0.0395176 ,  1.86336372,  0.71095086,
       -1.45093024,  0.67331925,  0.34522296,  0.79884796,  0.99412835,
       -0.83781945, -0.44204857,  1.37574074,  0.77737015, -0.01379314,
       -0.65928193, -1.12389596,  1.16602441,  1.39641448, -1.22641913,
       -0.40689392,  0.15854474,  0.40469101, -0.50680796,  0.3636981 ])
        
        self.assertEqual(mcvqoe.math.standard_error(x), 0.10056710785009866)
            
if __name__ == "__main__":
    with open('math-tests.xml','wb') as outf:
        unittest.main(
            testRunner=xmlrunner.XMLTestRunner(output=outf),
            failfast=False, buffer=False, catchbreak=False)
