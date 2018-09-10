#!/usr/bin/env python2.7
import socket
import sys
import struct
import numpy as np

TCP_IP= '192.168.50.101'
PORT= 5005
BUFFER_SIZE= 2000

sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((TCP_IP, PORT))

filename= open("testData.txt", "w")

while True:
	try:
		data= sock.recv(BUFFER_SIZE)
		str1= str(len(data)/4) + "f"
		Window= struct.unpack(str1, data)
		
		#for i in range(len(Window)):
		#	if Window[i]==10.0 and i<len(Window)-3:
		#		str2= str(Window[i+1]) + "," + str(Window[i+2])+ ","+ str(Window[i+3]) + "\n"
		#		print str2
		filename.write(str(Window))
	except Exception as e:
		print str(e)
		sock.close()
	


