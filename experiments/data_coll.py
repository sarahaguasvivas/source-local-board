#!/usr/bin/env python2.7
import socket
import sys
import struct
from multiprocessing import Pool, Manager, Value
import numpy as np
import time
import scipy
from sympy import *
import scipy.sparse.linalg as splinalg
import copy
from scipy import signal


BUFFER_SIZE=32000
NUM_SENSORS= 11
STEP_SIZE= 1.0/2000.0  # 1/ 1kHz

def same_events(q, count, cutoff=1.5):
    last_time = q[count][2] 
    res = sum([abs(last_time - q[c][2]) < cutoff for c in xrange(NUM_SENSORS)]) - 1
    return res

def read_data_window(ready_to_read,ready_to_source,IP, TCP_PORT, q, count):
    begin= True
    try:
        sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((IP, TCP_PORT))
        lastTime=0
        while True:
            while ready_to_read.value:
                t = time.time()
                try:
                    data=sock.recv(BUFFER_SIZE)
                    str1= str(len(data)/4) + "f"
                    Window= struct.unpack(str1, data)

                    yesno,lastTime= eventDetection(Window, lastTime)
                    if yesno:
                        q[count] = q[count][:1] + [Window] + [lastTime]
                        
                        if same_events(q,count)>=3:
                            #call the breeding function
                            
                            x1, x2, x3, y1, y2, y3, t12, t23, t31= Breeding(q, count)

                            u, i = source_localization(np.array([9., 5.]),x1,x2,x3,y1,y2,y3,t12,t23,t31,begin, count,rtol=1e-6,maxit=10,epsilon=1e-6)

                            begin=False
                            print "estimation: "+ str(u) + " iterations " + str(i) + " sensor: " + str(count) + " t12: "+ str(t12) + " t23: "+ str(t23) + " t31: "+ str(t31)
                         
                except Exception as e:
                    print "source_local failed sensor %s" %count
                    print str(e)
                    pass

    except Exception as e:
        print "connection failed s %s" %count
        sock.close()
        print str(e)
    
    if 'sock' in locals() or 'sock' in globals():
        sock.close()
        print "sensor %s unplugged" % count
    return None

def eventDetection(sensor, lastTime):
#######################################################
#           MODULE FOR ANOMALY DETECTION
#------------------------------------------------------
#   Using the Fast Wavelet Transform Algorithm to detect
#   events. I will be using the level 1 decomposition 
#   coefficient. 
#######################################################
    sensor= np.asarray(sensor, dtype= np.float64)
 
    yesno=False
    if np.amax(sensor)>0.2:
        newTime= time.time()
        if abs(lastTime-newTime)>0.001:
            yesno=True
            lastTime=newTime
    return yesno, lastTime

def Breeding(q, count):
#######################################################
#           MODULE FOR SENSOR BREEDING
#------------------------------------------------------
#   Here is where the random sampling will occur depen- 
#   ding on who detected an event first. This information
#   will be used as the "fitness" value.
#
#######################################################
    candidates=[]
    potential=[]
    for i in range(len(q)):
        try:
            if i != count:
                u= q[i][2]
                candidates.append(i)
                potential.append(1./abs(u-q[count][2])) 
        except Exception as e:
            print str(e)
    
    x1, y1= q[count][0]
    potential=np.array(potential)
    prob = potential/sum(potential)
    pair = np.random.choice(candidates, 2, replace=False, p=prob)
    x2,y2= q[pair[0]][0]
    x3,y3= q[pair[1]][0]
    ss1= q[count][1]
    ss2= q[pair[0]][1]
    ss3= q[pair[1]][1]
 
    ss1 = np.asarray(ss1, dtype=np.float64).flatten()
    ss2 = np.asarray(ss2, dtype=np.float64).flatten()
    ss3 = np.asarray(ss3, dtype=np.float64).flatten()
    t12= np.argmax(signal.correlate(ss1,ss2))*STEP_SIZE
    t23= np.argmax(signal.correlate(ss2,ss3))*STEP_SIZE
    t31= np.argmax(signal.correlate(ss3,ss1))*STEP_SIZE

    return float(x1), float(x2), float(x3), float(y1), float(y2), float(y3), float(t12), float(t23), float(t31)

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

def source_localization(u0,x1,x2,x3,y1,y2,y3,t12,t23,t31,begin, count,rtol,maxit,epsilon):
    ###################################################################
    # MODULE FOR SOURCE LOCALIZATION (using Newton-Krylov)
    # -----------------------------------------------------------------
    # This is my version of fsolve_newton() originally developed by Jed 
    # Brown (https://github.com/cucs-numpde/class). This is the routine
    #  that will do the source localization given three sensor signals
    ###################################################################
    if begin:
        filename= open("testSensor"+str(count)+".txt", "w")
    u= copy.copy(u0)
    Fu= F1(x1, x2, x3, y1, y2, y3, t23, t12, t31, u)
    
    norm0= np.linalg.norm(Fu)

    # Newton-Krylov with GMRES 
    for i in range(maxit):
        def Ju_fd(v): 
           return (F1(x1, x2, x3, y1, y2, y3, t23, t12, t31, u + epsilon*v)  - Fu) / epsilon
        Ju= splinalg.LinearOperator((len(Fu), len(u)), matvec=Ju_fd) 
        du, info = splinalg.gmres(Ju, Fu, x0=u)
        u -= du

        Fu= F1(x1, x2, x3, y1, y2, y3, t23, t12, t31, u)
        norm= np.linalg.norm(Fu)
        if begin:
            filename.write(repr(norm)+ "\n")
        if norm < rtol*norm0:
            break
    if i==maxit-1 and np.linalg.norm(u)>24:
        u= np.array([0,0])
    if begin:
        filename.close()
    return u, i

##########################################################
#    CONNECTING SENSORS USING THREADED SOCKET SERVER
##########################################################

print("Connecting to PZTs...")

if __name__ == "__main__":
    manager=Manager()
    q= manager.dict()

    ESPIPlist={}
    for i in range(NUM_SENSORS):
        q[i]=[]    

    TCP_PORT = 5005
    ESPIPlist[0]='192.168.50.129'
    ESPIPlist[1]='192.168.50.112'
    ESPIPlist[2]='192.168.50.45'
    ESPIPlist[3]='192.168.50.201'
    ESPIPlist[4]='192.168.50.173'
    ESPIPlist[5]='192.168.50.101'
    ESPIPlist[6]='192.168.50.131'
    ESPIPlist[7]='192.168.50.73'
    ESPIPlist[8]='192.168.50.193'
    ESPIPlist[9]='192.168.50.105'
    ESPIPlist[10]='192.168.50.36'
    
    # Position lists
    q[0]=q[0]+[(12.0, 0.0)] + [[]] + [float('inf')]
    q[1]=q[1]+[(12.0, 4.0)] + [[]]  + [float('inf')]
    q[2]=q[2]+[(6.0, 0.0)] + [[]]  + [float('inf')]
    q[3]=q[3]+[(0.0,0.0)] + [[]]  + [float('inf')]
    q[4]=q[4]+[(0.0, 4.0)] + [[]]  + [float('inf')]
    q[5]=q[5]+[(0.0, 8.0)] + [[]] + [float('inf')]
    q[6]=q[6]+[(6.0, 4.0)] + [[]] + [float('inf')]
    q[7]=q[7]+[(6.0, 8.0)] + [[]] + [float('inf')]
    q[8]=q[8]+[(12.0, 8.0)] + [[]]  + [float('inf')]
    q[9]=q[9]+[(18.0,0.0)] + [[]] + [float('inf')]
    q[10]=q[10]+[(18.0, 8.0)] + [[]] + [float('inf')]
    
    pool = Pool(processes=NUM_SENSORS)
    ready_to_read= manager.Value('ready_to_read', False)
    ready_to_read.value= False
    ready_to_source= manager.Value('ready_to_source', False)
    num_estimations= manager.Value('num_estimations',0)
    results = []
    for count in range(NUM_SENSORS):
        results.append(
        pool.apply_async(read_data_window, args=(ready_to_read,ready_to_source,ESPIPlist[count], TCP_PORT, q, count)) 
        )

    pool.close()
    ready_to_read.value= True
    for result in results:
        result.get()
    pool.join()

