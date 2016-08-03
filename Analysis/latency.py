###############################################################################################################################################################

#server log needs to be in same directory?

import sys #Needed to edit paths since multiple versions of Python have been downloaded
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64\DLLs')
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64')
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64\Lib')
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64\Lib\site-packages')

import time

###############################################################################################################################################################

mode = int(input('Which message should be analyzed? (1) part entered machine, (2) machine working, (3) machine done, (4) part in transit '))
if mode < 1 or mode > 4:
    print('defaulted to (1)')
mS = 'part entered machine' #***One of four possible message types
if mode == 2:
    mS = 'machine working'
if mode == 3:
    mS = 'machine done'
if mode == 4:
    mS = 'part in transit'

###############################################################################################################################################################

while 1:
    with open ('sf_server.log') as in_file:
        leftOff = 0
        epochTime = 0
        for line in reversed(list(in_file)):
            if mS in line:
                try:
                    count = line.count('"seqnum": ')
                    ST = (line.index('root:14') + 5)
                    CT = (line.index('"time": "') + 9)
                    SN = (line.index('"seqnum": ') + 10)
                    sequence = line[SN:SN + 6]
                    sequence2 = ''.join(c for c in sequence if c.isdigit())
                    serverTime = float(line[ST:(ST + 17)])
                    clientTime = float(line[CT:(CT + 17)])
                    latency = 1000 * round(serverTime - clientTime, 4) #serverTime - clientTime
                    print('seqnum: ' + sequence2 + '\tmsg: ' + mS + '\t' + str(latency) + ' ms')
                    break
                except Exception:
                    pass

###############################################################################################################################################################

    count = 0
    total2 = 0
    with open('sf_server.log') as in_line2:
        for line in reversed(list(in_line2)): #Reads from back to get last seqnum recorded; Acts as total
            count += line.count('"seqnum": ')
            try:
                if not total2: #Only defined once; Only causes issues when messages aren't received in order
                    totalIndex = line.index('"seqnum": ') + len('"seqnum": ')
                    total = line[totalIndex:totalIndex + 6] #seqnum is 6 characters long ar most
                    total2 = ''.join(c for c in total if c.isdigit())
            except Exception:
                pass
    print(str(count) + ' out of ' + total2 + ' messages received\t\t' + str(round(100 * (1 - count/float(total2 + '.0')), 6)) + '% loss\n==============================================================') #total2 + '.0' to allow for non-int division

###############################################################################################################################################################

    time.sleep(3)

###############################################################################################################################################################