# -*- coding: utf-8 -*-
"""
Created on Fri Jan 29 11:12:57 2021

@author: jkp4
"""

import unittest
import mcvqoe.math
import numpy as np

import pdb

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
if __name__ == "__main__":
    unittest.main()