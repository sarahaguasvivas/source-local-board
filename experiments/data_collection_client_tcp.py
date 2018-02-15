#!/usr/bin/env python2.7
import socket
import sys
import struct
from collections import deque
from multiprocessing import Pool, Queue
import numpy as np
from scipy import signal

global BUFFER_SIZE
BUFFER_SIZE= 32000
global WINDOW_SIZE
WINDOW_SIZE= 1000

def start_connections(sock, IP, PORT, count):
###################################################
# This function starts the TCP connection with the
# sensor and calls the event detection function.
# If there is an event, then it will put the window
# of data in the parallel queue; if not, then it will
# keep reading more data until there is an event.
# This function is meant to run in parallel.
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
            str1= "%sf" % BUFFER_SIZE/4 #4 being the number of bytes in float
            data=sock.recv(BUFFER_SIZE)
            data=struct.unpack(str1, data)
            total_data+=len(data)

            if total_data >= BUFFER_SIZE:
                num_lines+=1
                total_data-=BUFFER_SIZE
            # Keeping just a window of the data
            if j <= WINDOW_SIZE:
                Window.append(data)
                j+=1
            else:
                Window.append(data)
                Window.popleft()
            # Determine if there was an event happening in the structure
            if j >= WINDOW_SIZE:
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

    if right>250:
        yesno=1
        timelast=timenow
    else:
        yesno=0
    return yesno, sensor


##############################################################################
#       FUNCTIONS THAT WILL BE CALLED BY source_localization()
##############################################################################

#----------------------------------------------------
#      TRIANGULARIZATION STATEMENT EXPRESSION
#----------------------------------------------------
def FFF1(x1, x2, x3, y1, y2, y3, t23, t12, t31, x0,y0):
    d1= ((x1-x0)**2+(y1-y0)**2)**(1./2.)
    d2= ((x2-x0)**2+(y2-y0)**2)**(1./2.)
    d3= ((x3-x0)**2+(y3-y0)**2)**(1./2.)
    return t23*(d1-d2)-t12*(d2-d3)**2+(t31*(d2-d3)-t23*(d3-d1))**2+(t12*(d3-d1)-t31*(d1-d2))**2
#----------------------------------------------------
# EXPRESSION TO OPTIMIZE(DX and DY DERIVATIVES OF EXPRESSION ABOVE)
#-----------------------------------------------------
def F1(x1, x2, x3, y1, y2, y3, t23, t12, t31, u):
    x0= Symbol('x0')
    y0= Symbol('y0')
    dFdx = (FFF1(x1, x2, x3, y1, y2, y3, t23, t12, t31, x0,y0)).diff(x0)
    dFdy = (FFF1(x1, x2, x3, y1, y2, y3, t23, t12, t31, x0,y0)).diff(y0)
    
    dx= lambdify((x0,y0),dFdx)
    dy= lambdify((x0,y0),dFdy)
    return np.array([dx(u[0],u[1]),dy(u[0],u[1])])
#----------------------------------------------------
# JACOBIAN OF THE EXPRESSION TO OPTIMIZE (HESSIAN OF FFF1)
#----------------------------------------------------
def J1(x1, x2, x3, y1, y2, y3, t23, t12, t31, u):
    x0= Symbol('x0')
    y0= Symbol('y0')
    dFdx = FFF1(x1, x2, x3, y1, y2, y3, t23, t12, t31,x0,y0).diff(x0)
    dFdy = FFF1(x1, x2, x3, y1, y2, y3, t23, t12, t31, x0,y0).diff(y0)
    
    ddFdx= dFdx.diff(x0)
    ddFdy= dFdx.diff(y0)
    ddFxdy= dFdx.diff(y0)
    ddFydx= dFdy.diff(x0)
    
    dxx= lambdify((x0,y0),ddFdx)
    dyy= lambdify((x0,y0),ddFdy)
    dxy= lambdify((x0,y0),ddFxdy)
    dyx= lambdify((x0,y0),ddFydx)
    
    return np.array([[dxx(u[0],u[1]), dxy(u[0],u[1])],
                     [dyx(u[0],u[1]), dyy(u[0],u[1])]])

##############################################################################


def manager(q):
###############################################################################
# Manager keeps reading the queue until it has data from more than 2 sensors, 
# if it does, then it will call the source localization function. 
###############################################################################
    while True:
    # First check if the q has enough data readings
        data = q.get() # it is going to wait until the queue gets put data
        source_localization()
    return True

def source_localization(s1,s2,s3,u,x1,x2,x3,y1,y2,y3,t12,t23,t31,rtol,maxit,epsilon,verbose):
    ###################################################################
    # MODULE FOR SOURCE LOCALIZATION (using Newton-Krylov)
    # -----------------------------------------------------------------
    # This is my version of fsolve_newton() originally developed by Jed 
    # Brown (https://github.com/cucs-numpde/class). This is the routine
    #  that will do the source localization given three sensor signals
    ###################################################################
    u0= u.copy()
    Fu= F1(x1, x2, x3, y1, y2, y3, t23, t12, t31, u)
    JJ= J1(x1, x2, x3, y1, y2, y3, t23, t12, t31, u)
    
    norm0= np.linalg.norm(Fu)
    enorm_last= np.linalg.norm(u - np.array([1,1],dtype= np.float64))
    
    for i in range(maxit):
        
        def Ju_fd(v): # Preconditioning the Jacobian using Krylov 
            return (F1(x1, x2, x3, y1, y2, y3, t23, t12, t31, u + epsilon*v)  - 
                    Fu) / epsilon
    
        Ju = splinalg.LinearOperator((len(Fu),len(u)), matvec=Ju_fd)
    
        du, info = splinalg.gmres(JJ, Fu, x0=u, tol=1e-5, restart=10)
        
        if info != 0:
            raise RuntimeError('GMRES failed to converge: {:d}'.format(info))
        
        u -= du

        Fu= F1(x1, x2, x3, y1, y2, y3, t23, t12, t31, u)
        norm= np.linalg.norm(Fu)
        
        if verbose:
            enorm= np.linalg.norm(u - np.array([1,1]))
            print('Newton {:d} anorm {:6.2e} rnorm {:6.2e} eratio {:6.2f}'.
                  format(i+1, norm, norm/norm0, enorm/enorm_last**2))
            enorm_last= enorm
        if norm < rtol*norm0:
            break
        if np.isnan(norm):
            raise RuntimeError('Newton Raphson failed to converge: {:d}'.format(info)) 
    return u,i

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
#ESPlist[10].Posish= (18.25, 8.25)
#ESPlist[10].USB= 'DN03ECZM'

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
    ESPIPlist[10]='192.168.50.36'
    TCP_PORT = 5005
    
    sockets= [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(11)] 
    q = Queue()
    pool = Pool(processes=len(sockets)+1)
     
    count=0
    for sock in sockets:
        x = pool.apply_async(start_connections, args=(sock, q, ESPIPlist[count], TCP_PORT, count))
        count+=1
        # if has data from 3 sensors
    pool.start()

print "Ready for synch!"

pool.close()
for sock in sockets:
    sock.close()
