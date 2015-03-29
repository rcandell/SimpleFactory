'''
Created on Mar 28, 2015

@author: Rick Candell
@organization: NIST

'''

__ADDRS__ = []

def add_addrs(addr_list):
    __ADDRS__.extend(addr_list)
    
def push_addr(addr_tuple):
    __ADDRS__.append(addr_tuple)
    
def pop_addr():
    return __ADDRS__.pop()

