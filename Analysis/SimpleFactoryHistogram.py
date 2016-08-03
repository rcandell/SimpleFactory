# -*- coding: utf-8 -*-
#Created on Wed Jul 20 10:15:07 2016
#@author: nmc1

#*** Occasionally (<0.1%), client time subtracted shifts decimal places? (e.g. turns from 1469131829 to 14691); Only when buffer overflows & messages dump all at once
#Inputting a multiple of 7 uses suggested values

###############################################################################################################################################################

import sys #Needed to edit paths since multiple versions of Python have been downloaded
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64\DLLs')
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64')
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64\Lib')
sys.path.insert(0, 'C:\WinPython-64bit-3.4.3.2\python-3.4.3.amd64\Lib\site-packages')

import math
import matplotlib.pyplot as plt
import numpy as np

###############################################################################################################################################################

#Set up the histogram data from log file ***Make seperate script to save needed values in csv format so they don't have to be calculated each time
binNum = 0
histData = []
mode = 1
modeInput = int(input('(1) Milliseconds or (2) seconds? (1/2) '))
if (modeInput % 7) == 0:
    binNum = 128
    graphMax = .01
if modeInput == 1:
    mode = 1000
if not(modeInput == 1 or modeInput == 2) and (modeInput % 7): #If modeInput is neither 1, 2 or divisible by 7
    print('Defaulted to seconds')
if modeInput % 7:
    graphMax = float(input('Highest delay allowed? ({0:.2g} Recommended) '.format(.01 * mode)))

with open ('C:\git\SimpleFactory\sf_server.log') as in_file:

    """
    with open ('offset.log') as in_file2:
        leftOff = 0
        epochTime = 0 #Introduces variable; Arbitrary but less than first serverTime
    """

    for line in in_file:
        try:
            count = line.count('"seqnum": ') #Number of client messages per line
            ST = (line.index('root:14') + 5) #Start of serverTime string
            serverTime = float(line[ST:(ST + 17)]) #serverTime is 17 characters
            """
            if epochTime < serverTime: #Prevents calling of new offsetTime until serverTime passes epochTime
                for line2 in in_file2:
                    if not (leftOff % 2): #Each time two lines are logged; Every other line, starting from the first, contains local time
                        epochTime = int(line2[:10])
                        if epochTime > serverTime: #Isn't the next epochTime guaranteed to be larger than the next server time? (Goes up in steps of 5)
                            leftOff += 1
                            break
                    if (leftOff % 2): #On even lines (not 0-indexed), offsetTime is stored
                        offsetTime = float(line2[:-1])/1000 #Converts from ms to s
                    leftOff += 1
            serverTime += offsetTime

#bash side
rm offset.log
while :; do
    (date +%s && echo $(ntpq -p) | awk '{print $20}') >> offset.log
    sleep 5
done
            """
            clientTime = line.split('"time": "')
            for i in range(count): #Once per message on the line
                latency = (mode * (round(serverTime - float(clientTime[i + 1][:17]), 6))) #serverTime - clientTime
                if latency < graphMax:
                    histData.append(latency)
        except ValueError:
            pass
        except IndexError:
            pass
        except Exception as e:
            print(e)

###############################################################################################################################################################

#Create the histogram variables ***Can be used to determine the values that split the data
if modeInput % 7:
    while not binNum:
        try:
            binNum = int(input('How many bins should be made? ')) #Changes number of bins and therefore increment ***For dynamic, leave out of Main()
            if binNum > 0:
                break
            binNum = 0
            print('The number of bins has to be positive')
        except Exception:
            pass
binRotation = 0
if binNum > 16:
    binRotation = 90 #Rotates the labels if a minimum is reached
sectionSize = math.ceil(binNum/32) #Limits how many ticks are made for performance/readability; ***32 is arbitrary max number of ticks

###############################################################################################################################################################

#Create the histogram
y, x, _ = plt.hist(histData, bins = binNum)
binMax = x.max()
binMin = x.min()
binTickMax = (binMax - (((binNum % sectionSize)/float(binNum)) * (binMax - binMin))) #Remove one bin width for every extra bin; binNum floated to prevent integer division errors
plt.xticks(np.linspace(binMin, binTickMax, num = (binNum/sectionSize + 1)), rotation = binRotation) #If there are more than 32 bins, add one tick per sectionSize; binTickMax defined earlier for readability
plt.xlabel('Time Delay (s), from ' + str(round(binMin, 5)) + 's to ' + str(round(binMax, 5)) + 's', fontsize = 18)
plt.ylabel('# of cases', fontsize = 18)
plt.title('Histogram of Time Delay, avg. = ' + str(round(np.mean(histData), 5)) +'s; max = ' + str(graphMax) + 's', fontsize = 24)
if mode == 1000:
    plt.xlabel('Time Delay (ms), from ' + str(round(binMin, 3)) + 'ms to ' + str(round(binMax, 3)) + 'ms', fontsize = 18)
    plt.title('Histogram of Time Delay, avg. = ' + str(round(np.mean(histData), 3)) + 'ms; max = ' + str(graphMax) + 'ms', fontsize = 24)
plt.axis([binMin, binMax, 0, y.max() * 1.1])
plt.grid(True)
plt.show()