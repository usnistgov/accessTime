
from .Probabilityiser import PBI
from .QoEsim import ImpairmentParam
from numpy import inf

description = 'An impairment to represent a \'flakey\' channel. It is recommended to not use this as a pre impairment.'

impairment_type = 'generic'

parameters = {
    'P_a1'     : ImpairmentParam(1.0, float, 'range', min_val=0.0, max_val=1.0,
                                 interval = 0.001,
                                 description = 'Original probability transitioning into a transmitting state.'
                                ),
    'P_a2'     : ImpairmentParam(1.0, float, 'range', min_val=0.0, max_val=1.0, interval = 0.001,
                                 description = 'Probability transitioning into a transmitting state.',
                                ),
    'P_r'      : ImpairmentParam(1.0, float, 'range', min_val=0.0, max_val=1.0, interval = 0.001,
                                 description = 'Probability of remaining in a transmitting state.',
                                ),
    'interval' : ImpairmentParam(1.0, float, 'positive', interval = 0.001,
                                description = 'How often state transitions are evaluated.'
                                ),
}

def create_impairment(P_a1=1, P_a2=None, P_r=1, interval=1):

    impairment_class = PBI(P_a1=P_a1, P_a2=P_a2, P_r=P_r, interval=interval)
    
    return impairment_class.process_audio
