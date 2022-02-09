# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 08:20:53 2021

@author: cjg2
"""
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

import json
import numpy as np
import os
import pandas as pd
import tempfile 

from mcvqoe.hub.eval_app import app

import mcvqoe.hub.eval_shared as eval_shared

#-----------------------[Begin layout]---------------------------

measurement = 'diagnostics'
layout = eval_shared.layout_template(measurement)

def format_diagnostic_results(diagnostics_eval, digits=4):
    """
    Format results from Test_Stats to be in HTML.

    Parameters
    ----------
    diagnostics_eval : 
        DESCRIPTION.

    Returns
    -------
    children : html.Div
        DESCRIPTION.
    """
   
    
