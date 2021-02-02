#!/usr/bin/env python


import mcvqoe
import mcvqoe.utilities
import mcvqoe.simulation
import os.path
import unittest
import datetime
import tempfile


#fake test class for logging purposes
class FakeTest:
    no_log=()
    
    def __init__ (self):
        sim_obj=mcvqoe.simulation.QoEsim()
        self.ri=sim_obj
        self.audioInterface=sim_obj
    

class LogTest(unittest.TestCase):

    def test_write_read_error(self):
        #make a fake test class
        dummy = FakeTest()

        info=mcvqoe.write_log.fill_log(dummy)
        self.assertEqual(info['RI version'],mcvqoe.version)
        self.assertEqual(info['filename'],os.path.basename(__file__))

        info['test']='unittest'
         #give our test a date
        info['Tstart']=datetime.datetime(1953, 3, 24)
        info['Pre Test Notes']='Starting test, hopefully nothing goes too wrong\n'
        
        #make a temp dir to store logs in
        with tempfile.TemporaryDirectory() as tmp_dir:
            
            mcvqoe.write_log.pre(info,outdir=tmp_dir)
            self.assertTrue(os.path.exists(os.path.join(tmp_dir,'tests.log')))

            #add post notes
            info['Error Notes']='Things went horribly wrong\n'

            mcvqoe.write_log.post(info,outdir=tmp_dir)
            #TODO: check if the file got bigger?
                    
            ls=mcvqoe.utilities.log_search(os.path.join(tmp_dir,'tests.log'),LogParseAction='Error')
            
            self.assertEqual(ls.Qsearch('operation','unittest'),set([0]))
            self.assertTrue(ls.log[0]['complete'])
            self.assertTrue(ls.log[0]['error'])
            self.assertEqual(ls.log[0]['date'],info['Tstart'])

    def test_write_read_normal(self):
        #make a fake test class
        dummy = FakeTest()

        info=mcvqoe.write_log.fill_log(dummy)
        self.assertEqual(info['RI version'],mcvqoe.version)
        self.assertEqual(info['filename'],os.path.basename(__file__))

        info['test']='unittest'
         #give our test a date
        info['Tstart']=datetime.datetime(1953, 8, 21)
        info['Pre Test Notes']='Perhaps this works now\n'
        
        #make a temp dir to store logs in
        with tempfile.TemporaryDirectory() as tmp_dir:
            
            mcvqoe.write_log.pre(info,outdir=tmp_dir)
            self.assertTrue(os.path.exists(os.path.join(tmp_dir,'tests.log')))

            info['Post Test Notes']='Everything is as it should be\n'
            mcvqoe.write_log.post(info,outdir=tmp_dir)
            #TODO : check that log got bigger?
                    
            ls=mcvqoe.utilities.log_search(os.path.join(tmp_dir,'tests.log'),LogParseAction='Error')
            
            self.assertEqual(ls.Qsearch('operation','unittest'),set([0]))
            self.assertTrue(ls.log[0]['complete'])
            self.assertFalse(ls.log[0]['error'])
            self.assertEqual(ls.log[0]['date'],info['Tstart'])

    
if __name__ == "__main__":
    unittest.main()