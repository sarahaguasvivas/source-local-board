#!/usr/bin/env python2.7
import socket
import sys
import struct
from collections import deque
from multiprocessing import Pool, Manager
import numpy as np
from scipy import signal

global BUFFER_SIZE
BUFFER_SIZE= 32000
global WINDOW_SIZE
WINDOW_SIZE= 1000
global ready_to_read
ready_to_read=False
NUM_SENSORS= 11

def read_data_window(IP, TCP_PORT, q, count, ready_to_read=False):
    try:
        
        sock= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((IP, TCP_PORT))
        print "sensor %s is connected" % count
        j=0
        while True:
            while not ready_to_read:
                pass    
            Window=deque([])
            total_data=0
            num_lines=0
            try:
                data=sock.recv(BUFFER_SIZE)
                str1= str(len(data)/4) + "f"
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
                    yesno, impact_data= eventDetection(Window)
                    if yesno==1:
        #   figure out how to keep the table organized
        #                q.put((count, Window))
            sock.close()
            except:
                print "some data lost from sensor %s" % count
    except:
        print "sensor %s could not connect" % count
    return None

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
        print "tap!"
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
#ESPlist[1].Posish= (12, 4)
#ESPlist[2].USB= 'DN03FLZJ'
#ESPlist[2].Posish= (6, 0)
#ESPlist[3].USB= 'DN03FM0N'
#ESPlist[3].Posish= (0,0)
#ESPlist[4].USB= 'DN03FLZV'
#ESPlist[4].Posish= (0, 4)
#ESPlist[5].USB= 'DN03FM0V'
#ESPlist[5].Posish= (0, 8)
#ESPlist[6].USB= 'DN03ECYN'
#ESPlist[6].Posish= (6, 4)
#ESPlist[7].USB= 'DN03FLZI'
#ESPlist[7].Posish= (6, 8)
#ESPlist[8].USB= 'DN03FM0O'
#ESPlist[8].Posish= (12, 8)
#ESPlist[9].USB= 'DN03FM0W'
#ESPlist[9].Posish= (18,0)
#ESPlist[10].Posish= (18, 8)
#ESPlist[10].USB= 'DN03ECZM'

##########################################################
#    CONNECTING SENSORS USING THREADED SOCKET SERVER
##########################################################

print "Connecting to PZTs..."

if __name__ == "__main__":
    manager=Manager()
    q= manager.dict()
    
    for i in range(NUM_SENSORS):
        q[i]=[]    

    TCP_PORT = 5005
    q[0]= q[0]+'192.168.50.129'
    q[1]= q[1]+'192.168.50.112'
    q[2]= q[2]+'192.168.50.45'
    q[3]= q[3]+'192.168.50.201'
    q[4]= q[4]+'192.168.50.173'
    q[5]= q[5]+'192.168.50.101'
    q[6]= q[6]+'192.168.50.131'
    q[7]= q[7]+'192.168.50.73'
    q[8]= q[8]+'192.168.50.193'
    q[9]= q[9]+'192.168.50.105'
    q[10]= q[10]+'192.168.50.36'
    
    # Position lists
    q[0]=q[0]+[(12, 0)]
    q[1]=q[1]+[(12, 4)]
    q[2]=q[2]+[(6, 0)]
    q[3]=q[3]+[(0,0)]
    q[4]=q[4]+[(0, 4)]
    q[5]=q[4]+[(0, 8)]
    q[6]=q[6]+[(6, 4)]
    q[7]=q[7]+[(6, 8)]
    q[8]=q[8]+[(12, 8)]
    q[9]=q[9]+[(18,0)]
    q[10]=q[10]+[(18, 8)]

    pool = Pool(processes=len(sockets))
     
    for count in range(NUM_SENSORS):
        x= pool.apply_async(read_data_window, args=(ESPIPlist[count], TCP_PORT, q, count, ready_to_read=False)) 
        pool.close()
    ready_to_read=True

pool.join()
for sock in sockets:
    sock.close()
