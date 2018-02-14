#!/usr/bin/env python2.7
import socket
import sys
import struct
from collections import deque
from multiprocessing import Pool, Queue

def start_connections(socket, q, count):
    while True:
        #Event Detection
        #Read Data from Socket
        #If event is detected, put data on queue
        pass

def eventDetection(q):
    return True

def manager(q):
  #get the data and  
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

BUFFER_SIZE = 1460
WINDOW_SIZE= 1000

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
    
   # for sock in sockets:
   #     try:
   #         sock.connect((ESPIPlist[i], TCP_PORT))
   #         print "sensor %s is connected" % i
   #     except:
   #         print "sensor %s could not connect" % i
   #         continue

    q = Queue()
    pool = Pool(processes=len(sockets)+1)
    #pool.apply_async(manager, args=(q,))
    count=0
    for sock in sockets:
        x = pool.apply_async(start_connections, args=(sock, q, ESPIPlist[count], TCP_PORT))
        # if has data from 3 sensors
        count+=1 
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

