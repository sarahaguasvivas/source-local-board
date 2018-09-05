#!/usr/bin/env python2.7
import socket
import sys
import struct

TCP_IP= '192.168.50.101'
PORT= 5005
BUFFER_SIZE= 4000

sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((TCP_IP, PORT))

while True:
	try:
		data= sock.recv(BUFFER_SIZE)
		str1= str(len(data)/4) + "f"
		Window= struct.unpack(str1, data)
		AllData= []
		for i in range(len(Window)):
			if Window[i]==10.0 and i<len(Window)-3:
				AllData+= [Window[i+1], Window[i+2], 
						Window[i+3]] 
#				AllData+= Window[i+2]
#				AllData+= Window[i+3]
								
		print AllData
	except Exception as e:
		print str(e)
		sock.close()
	


