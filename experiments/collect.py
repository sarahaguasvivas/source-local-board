#!/usr/bin/env python2.7
import socket
import sys
import struct

TCP_IP= '192.168.50.101'
PORT= 5005
BUFFER_SIZE= 3000
filename= open("testData.txt", "w")

sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((TCP_IP, PORT))

while True:
	try:
		data= sock.recv(BUFFER_SIZE)
		str1= str(len(data)/4) + "f"
		Window= struct.unpack(str1, data)
		print(Window)	
	
	except:
		sock.close()
		filename.close()	
	


