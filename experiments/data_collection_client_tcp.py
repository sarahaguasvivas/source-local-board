#!/usr/bin/env python2.7
import socket
import sys
import struct
from collections import deque
from multiprocessing import Pool, Queue
import numpy as np
from scipy import signal

global BUFFER_SIZE= 32000
global WINDOW_SIZE= 1000

def start_connections(sock, IP, PORT, count):
###################################################
# This function starts the TCP connection with the
# sensor and calls the event detection function.
# If there is an event, then it will put the window
# of data in the parallel queue; if not, then it will
# keep reading more data until there is an event.
# This function is meant to run in parallel
###################################################
    try:
        sock.connect((IP, PORT))
    except:
        print "sensor %s could not connect" % count
    return True

def read_data_window(sock, q, count):
    j=0
    while True:
        Window=deque([])
        total_data=0
        num_lines=0
        try:
            data=sock.recv(BUFFER_SIZE)
            data=struct.unpack('100f', data)
            total_data+=len(data)

            if total_data>= BUFFER_SIZE:
                num_lines+=1
                total_data-=BUFFER_SIZE
            #Keeping just a window of the data
            if j<= WINDOW_SIZE:
                Window.append(data)
                j+=1
            else:
                Window.append(data)
                Window.popleft()
            #Determine if there was an event happening in the structure
            if j>=WINDOW_SIZE:
                yesno, impact_data= eventDetection(data)
                if yesno==1:
                    q.put((count, Window))
                    manager(q)
        except:
            print "some data lost from sensor %s" % count

    return True

def eventDetection(sensor):
#######################################################
#           MODULE FOR ANOMALY DETECTION
#------------------------------------------------------
#   Using the Fast Wavelet Transform Algorithm to detect
#   events. I will be using the level 1 decomposition 
#   coefficient. 
#######################################################
    widths= np.arange(1,31)
    sensor= np.array(sensor)
    cwtmatr= signal.cwt(sensor.astype(int), signal.ricker, widths)

    yesno=0
    left= right
    right= np.linalg.norm(cwtmatr[:, -1], np.inf)

    if right-left >250 and np.abs(timenow-timelast)>2000:
        yesno=1
        timelast=timenow
        sensdata=sensor[-1]
    else:
        yesno=0
        sensdata= np.zeros_like(right)
    return yesno, sensor_data

def manager(q):
###############################################################################
# Manager keeps reading the queue until it has data from more than 2 sensors, 
# if it does, then it will call the source localization function. 
###############################################################################
    while True:
        data = q.get() # it is going to wait until the queue gets put data
        source_localization()


def source_localization(q):
    return True

#class ESP:
#    def __init__(self, IP1, USB1, Posish1, Cardinal1):
#        self.IP= IP1
#        self.USB= USB1
#        self.Posish= Posish1
#        self.Cardinal= Cardinal1
#ESPlist[0].USB= 'DN03FM0A'
#ESPlist[0].Posish= (12, 0)
#ESPlist[1].USB= 'DN02YZBQ'
#ESPlist[1].Posish= (12, 4.25)
#ESPlist[2].USB= 'DN03FLZJ'
#ESPlist[2].Posish= (6.25, 0)
#ESPlist[3].USB= 'DN03FM0N'
#ESPlist[3].Posish= (0,0)
#ESPlist[4].USB= 'DN03FLZV'
#ESPlist[4].Posish= (0, 4.25)
#ESPlist[5].USB= 'DN03FM0V'
#ESPlist[5].Posish= (0, 8.25)
#ESPlist[6].USB= 'DN03ECYN'
#ESPlist[6].Posish= (6.25, 4.25)
#ESPlist[7].USB= 'DN03FLZI'
#ESPlist[7].Posish= (6.25, 8.25)
#ESPlist[8].USB= 'DN03FM0O'
#ESPlist[8].Posish= (12, 8.25)
#ESPlist[9].USB= 'DN03FM0W'
#ESPlist[9].Posish= (18.25,0)

#BUFFER_SIZE = 1460
#WINDOW_SIZE= 1000

if len(sys.argv) != 2:
	print "python data_collection_client.py <FILENAME>"
	sys.exit()

filename = sys.argv[1]

##########################################################
#    CONNECTING SENSORS USING THREADED SOCKET SERVER
##########################################################

print "Connecting to PZTs..."

if __name__ == "__main__":

    ESPIPlist= {}
    ESPIPlist[0]= '192.168.50.129'
    ESPIPlist[1]= '192.168.50.112'
    ESPIPlist[2]= '192.168.50.45'
    ESPIPlist[3]= '192.168.50.201'
    ESPIPlist[4]= '192.168.50.173'
    ESPIPlist[5]= '192.168.50.101'
    ESPIPlist[6]='192.168.50.131'
    ESPIPlist[7]='192.168.50.73'
    ESPIPlist[8]='192.168.50.193'
    ESPIPlist[9]='192.168.50.105'
    TCP_PORT = 5005
    
    sockets= [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(10)]
    
    q = Queue()
    pool = Pool(processes=len(sockets)+1)
     
    count=0
    for sock in sockets:
        x = pool.apply_async(start_connections, args=(sock, q, ESPIPlist[count], TCP_PORT, count))
        count+=1
        # if has data from 3 sensors
    pool.start()
    x.get()
    pool.join()

print "Ready for synch!"

######################################
#       SYNCHRONIZING SENSORS
######################################



######################################
#          EVENT DETECTION
######################################



######################################
#        READING ONLINE DATA
######################################

total_data = 0 
num_lines = 0
str1= "%sf"% BUFFER_SIZE/4 #4 being the number of bytes in float 
try:
    while True:
        for sock in sockets:
            data = sock.recv(BUFFER_SIZE)
            data=struct.unpack("100f", data)
            print data
            total_data += len(data)
		
            if total_data >= BUFFER_SIZE:
			    num_lines += 1
			    total_data -= BUFFER_SIZE

except:
	print "Exception!"

for sock in sockets:
    sock.close()

