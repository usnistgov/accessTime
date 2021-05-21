import warnings

#plugin for clean channel

#No channel, no delay
standard_delay=0

def simulate_audio_channel(sim,tx_data):
    if(sim.channel_impairment):
        warnings.warn('There is no channel for the \'clean\' option. can not use channel_impairment')
    if(sim.channel_rate):
        warnings.warn('For \'clean\' there is no rate. \'channel_rate\' option ignored')

    return tx_data