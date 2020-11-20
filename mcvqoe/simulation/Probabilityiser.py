#!/usr/bin/env python

import random

class PBI: 
    STATE_INVALID=0
    STATE_G0=1
    STATE_G1=2
    STATE_H=3
                
    def __init__(self):
        #time in seconds between state machine evaluations
        self.interval=1
        self.initial_state()
        self.P_a1=1
        self.P_a2=1
        self.P_r=1
        
    def initial_state(self):
        self.state=self.STATE_G0
        
    def process_audio(self,data,fs):
        #set to initial state
        self.initial_state()
        
        #calculate the number of samples in each chunk
        chunk_len=int(round(fs*self.interval))
        
        start=range(0,len(data),chunk_len)
        stop=list(range(chunk_len,len(data),chunk_len))
        #add end of array to stop
        stop.append(len(data))
        
        for s,e in zip(start,stop):
            self.update_state()
            if(self.state!=self.STATE_H):
                data[s:e]=0
                
        return data
    
    def update_state(self):
        #generate random number for state transition
        r=random.random()
        #select next state based on current state
        if(self.state==self.STATE_G0):
            if(r<self.P_a1):
                #transition into H state
                self.state=self.STATE_H
            else:
                #stay in G0 state
                pass
        elif(self.state==self.STATE_G1):
            if(r<self.P_a2):
                #transition into H state
                self.state=self.STATE_H
            else:
                #stay in G1 state
                pass
        elif(self.state==self.STATE_H):
            if(r<self.P_r):
                #stay in H state
                pass
            else:
                #transition into G1 state
                self.state=self.STATE_G1