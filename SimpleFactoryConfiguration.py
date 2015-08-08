'''
Created on Mar 29, 2015

@author: rnc4
'''

import json

class SimpleFactoryConfiguration:
    def __init__(self, path="factory_config.json"):
        self.client_addrs = []
        with open(path) as data_file:    
            self.data = json.load(data_file)
            self.parse()        
 
    def parse(self):
        self.RANDOM_SEED= self.data["RANDOM_SEED"]
        self.RUN_RT = self.data["RUN_RT"]
        self.SIM_RT_FACTOR= self.data["SIM_RT_FACTOR"]
        self.NUM_PARTS= self.data["NUM_PARTS"]
        self.NUM_MACHINES= self.data["NUM_MACHINES"] 
        self.NUM_STATIONS= self.data["NUM_STATIONS"] 
        self.WORKTIME= self.data["WORKTIME"]      
        self.T_INTER= self.data["T_INTER"]  
        self.server_addr = (self.data['server_addr']['host'], self.data['server_addr']['port'])
        '''
        for ii in range(0, len(self.data['client_addrs'])):
            host = self.data['client_addrs'][ii]['host']
            port = self.data['client_addrs'][ii]['port']
            self.client_addrs.append((host,port))
        self.data = None
        '''
        