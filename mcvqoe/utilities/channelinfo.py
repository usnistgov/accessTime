#!/usr/bin/env python

import argparse
import mcvqoe.simulation

def main():
    parser = argparse.ArgumentParser(
            description='Get info on mcvqoe channel plugins. If a plugin name' +
                        ' is given, print info on that plugin. Otherwise list' +
                        ' available plugins.')
    parser.add_argument(
    'chan', default=None, nargs="?", metavar='CHAN',
    help='audio channel to print info for.')
    
    args = parser.parse_args()
    
    #create qoesim object
    sim_obj=mcvqoe.simulation.QoEsim()
    #get channel technologies
    techs=sim_obj.get_channel_techs()
    #check what info we are going to print
    if(args.chan):
        #check that this tech is valid
        if(args.chan not in techs):
            print(f'Error : {args.chan} is not a valid channel technology')
            exit(1)

        mod = sim_obj._get_chan_mod(args.chan)
        print(f'module name : {mod.__name__}')

        (def_rate,rates)=sim_obj.get_channel_rates(args.chan)
        print(f'Default rate : {def_rate}')
        print(f'Possible rates : {rates}')

        #everything is fine
        exit(0)
    else:
        print(f'Channel technologies : {techs}')

        #everything is fine
        exit(0)


if __name__ == "__main__":
    main()