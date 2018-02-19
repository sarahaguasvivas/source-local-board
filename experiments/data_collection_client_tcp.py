#!/usr/bin/env python2.7
import socket
import sys
import struct
from collections import deque
from multiprocessing import Pool, Manager, Value
import numpy as np
from scipy import signal


global BUFFER_SIZE
BUFFER_SIZE=32000
global WINDOW_SIZE
WINDOW_SIZE=300
global NUM_SENSORS
NUM_SENSORS= 11

def read_data_window(ready_to_read, IP, TCP_PORT, q, count):
    try:
        sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((IP, TCP_PORT))
        j=0
        Window= deque([])
        while True:
            while ready_to_read.value:
                total_data=0
                num_lines=0
                try:
                    data=sock.recv(BUFFER_SIZE)
                    str1= str(len(data)/4) + "f"
                    data= struct.unpack(str1, data)
                    total_data+=len(data)
                    if total_data >= BUFFER_SIZE:
                        num_lines+=1
                        total_data-=BUFFER_SIZE
                # Keeping just a window of the data
                    if j <= WINDOW_SIZE:
                        q[count]=q[count][:1]
                        Window.append(data)
                        j+=len(data)
                    else:
                        Window.append(data)
                # Popleft will remove all of the data added before
                        Window.popleft()
                # Determine if there was an event happening in the structure
                    if j >= WINDOW_SIZE:
                        yesno= eventDetection(Window)
                        if yesno:
                            q[count]= q[count] + [Window]
                except:
                    pass
    except:
        pass
    
    if 'sock' in locals() or 'sock' in globals():
        sock.close()
        print "sensor %s unplugged" % count
    return None

def eventDetection(sensor):
#######################################################
#           MODULE FOR ANOMALY DETECTION
#------------------------------------------------------
#   Using the Fast Wavelet Transform Algorithm to detect
#   events. I will be using the level 1 decomposition 
#   coefficient. 
#######################################################
    sensor= np.array(sensor[0])
    grad= np.gradient(sensor)
    yesno=False
    print grad
    if sensor.max()>0.3:
        yesno=True
        print "Tap!"
    return yesno


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

##########################################################
#    CONNECTING SENSORS USING THREADED SOCKET SERVER
##########################################################

print "Connecting to PZTs..."

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
    q[0]=q[0]+[(12, 0)]
    q[1]=q[1]+[(12, 4)]
    q[2]=q[2]+[(6, 0)]
    q[3]=q[3]+[(0,0)]
    q[4]=q[4]+[(0, 4)]
    q[5]=q[5]+[(0, 8)]
    q[6]=q[6]+[(6, 4)]
    q[7]=q[7]+[(6, 8)]
    q[8]=q[8]+[(12, 8)]
    q[9]=q[9]+[(18,0)]
    q[10]=q[10]+[(18, 8)]

    pool = Pool(processes=NUM_SENSORS)
    ready_to_read= manager.Value('ready_to_read', False)
 
    for count in range(NUM_SENSORS):
        x= pool.apply_async(read_data_window, args=(ready_to_read, ESPIPlist[count], TCP_PORT, q, count)) 
    pool.close()
    ready_to_read.value= True

    pool.join()
