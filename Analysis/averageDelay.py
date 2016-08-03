###############################################################################################################################################################

import sys #Needed to edit paths since multiple versions of Python have been downloaded
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64\DLLs')
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64')
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64\Lib')
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64\Lib\site-packages')

import numpy as np

###############################################################################################################################################################

mode = int(input('Which message should be analyzed? (1) part entered machine, (2) machine working, (3) machine done, (4) part in transit '))
histData = []
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

with open ('C:\git\SimpleFactory\sf_server.log') as in_file:
    """
    with open ('offset.log') as in_file2:
        leftOff = 0
        epochTime = 0
        """
    for line in in_file:
        if mS in line:
            try:
                count = line.count('"seqnum": ')
                ST = (line.index('root:14') + 5)
                CT = (line.index('"time": "') + 9)
                PT = (line.index('"msg": "') + 8)
                PT2 = line.index('", "part": ') #***Varies between each test since messages aren't always received in the same order***
                SN = (line.index('"seqnum": ') + 10)
                SN2 = (line.index(', "machine": '))
                serverTime = float(line[ST:(ST + 17)])
                """
                if epochTime < serverTime:
                    for line2 in in_file2:
                        if not (leftOff % 2):
                            epochTime = int(line2[:10])
                        if epochTime > serverTime: #Isn't the next epoch time guaranteed to be larger than the next server time? (Goes up in steps of 5)
                            leftOff += 1
                            break
                        if (leftOff % 2):
                            offsetTime = float(line2[:-1])/1000
                        leftOff += 1
                serverTime += offsetTime
                """
                clientTime = float(line[CT:(CT + 17)])
                seqnum = line[SN:SN2]
                message = line[PT:PT2]
                latency = 1000 * round(serverTime - clientTime, 6)
                #print('seqnum: ' + seqnum + '\t' + message + '\t' + str(latency) + ' ms') #***Extra Information
                if latency < 10:
                    histData.append(latency)
            except Exception:
                pass
print('"' + mS + '" message analyzed')
print('avg. is ' + str(round(np.mean(histData), 3)) + ' ms')

###############################################################################################################################################################