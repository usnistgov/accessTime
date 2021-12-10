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

def format_diagnostic_results(m2e_eval, digits=6):
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
    
   RX_Name = eval_shared.pretty_numbers(m2e_eval.mean, digits)
   A_Weight = eval_shared.pretty_numbers(m2e_eval.ci, digits)
   FSF_Scores
   children = html.Div([
        html.H6('Rx Clip Name'),
        html.Div(f'{pretty_mean} seconds'),
        html.H6('A Weight'),
        html.Div(f'{pretty_ci} dBA'),
        html.H6('Thinning factor'),
        html.Div(f'{m2e_eval.common_thinning}'),
        html.Div('TODO: Do something smarter when common thinning factor is not found'),
        ],
        style=eval_shared.style_results,
        # className='six columns',
        )
    return children

