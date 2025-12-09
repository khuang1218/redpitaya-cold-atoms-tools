#!/usr/bin/python

import sys
import numpy as np
import time
import redpitaya_scpi as scpi
import matplotlib.pyplot as plot

#PID Function defined here...

def Pid(error, integral, Kp, Ki):
   output=error*Kp
   output+=integral*Ki
   return output

#IP address of Red Pitaya read by system here
rp_s = scpi.scpi(sys.argv[1])

start = time.time()

#Eseential Parameters Initialisation
'''peak=[0, 0, 0, 0]
peak_pos=[0, 0, 0, 0]
Dc=[0.9, 0.0, 0.0]'''

peak=np.array([0, 0, 0, 0])
peak_pos=np.array([0, 0, 0, 0])
Dc=np.array([0.9, 0.0, 0.0])

#Kp=[0.00000005, -0.001, 0.0]
#Ki=[0.00001, -0.01, 0.0] and set_point[0]=500, actual = 500 around

Kp=[0.00000005, -0.0000001, 0.0]
Ki=[0.00001, -0.01, 0.0]

#Kp=[0.0000000000884, -0.0000001, 0.0]
#Ki=[0.0000827, -0.01, 0.0]   ### for 679

#Kp=np.array([0.0000000000895, -0.000043, 0.0])
#Ki=np.array([0.0000827, -0.51, 0.0]) ### for 679

#Kp=np.array([0.00000000007, -0.0000003, 0.0])
#Ki=np.array([0.00009, -0.30, 0.0])




integral=np.array([0.0, 0.0, 0.0])
error=np.array([0.0, 0.0, 0.0])
relative_pos_peak=np.array([0.0, 0.0])
relative_pos_set=np.array([0.0, 0.0])

'''integral=[0, 0, 0]
error=[0.0, 0.0, 0.0]
relative_pos_peak=[0.0, 0.0]
relative_pos_set=[0.0, 0.0]'''

rp_s.tx_txt('ANALOG:PIN AOUT0' + ','+str(Dc[0])) #set 0 point to 0.9 V, so that after negative voltage, range would be 0-1.8 V 

#rp_s.tx_txt('OUTPUT2:STATE ON')
rp_s.tx_txt('OUTPUT1:STATE ON')
#rp_s.tx_txt('SOUR2:VOLT:OFFS ' +str(Dc[0]))
rp_s.tx_txt('SOUR1:VOLT:OFFS ' +str(Dc[1]))
#rp_s.tx_txt('SOUR1:VOLT:OFFS 0.9')
#print('working')



# Taking input parameters from command line, mainly initial peak postions and no. of loop
set_point=np.array([0, 0])
set_point[0] = int(sys.argv[2])
set_point[1] = int(sys.argv[3])-set_point[0]
#set_point[1] = 10000
'''set_point=[0, 0]
set_point[0] = float(sys.argv[2])
set_point[1] = float(sys.argv[3])-set_point[0]'''

loop = int(sys.argv[4])

#ki = float(sys.argv[5])
#print(set_point[0])
# Main Program Starts here for Data acquisition on external Trigger

run=0
#on_off=1
firstpeak=[set_point[0]]
secondpeak=[set_point[1]+set_point[0]]
#triggerlocation=[0]
xpeak=[0.0]
#figs=[]
#outputfile = open('bufferfile.csv', 'w')
while 1:
    
    '''if on_off :
        on_off=0
        rp_s.tx_txt('ANALOG:PIN AOUT0,1.0')
    else:
        on_off=0
        rp_s.tx_txt('ANALOG:PIN AOUT0,0.5')'''
        

    rp_s.tx_txt('ACQ:RST')
    rp_s.tx_txt('ACQ:DATA:FORMAT ASCII')
    rp_s.tx_txt('ACQ:DATA:UNITS VOLTS')
    rp_s.tx_txt('ACQ:DEC 16')
    #print (set_point[0])

    rp_s.tx_txt('ACQ:TRIG:LEVEL 1')
    rp_s.tx_txt('ACQ:TRIG:DLY 8192')
    rp_s.tx_txt('ACQ:START')
    #print (set_point[1])

    time.sleep(0.099) #pause of 90 ms to acquire the fresh samples in buffer : Calculate it using decimation and sampling, put it only mentioned values like 64
 
    rp_s.tx_txt('ACQ:TRIG EXT_PE')
    #rp_s.tx_txt('ACQ:TRIG CH1_PE')
    #print ("working3")


    while 1:
        #print ("working4")
        rp_s.tx_txt('ACQ:TRIG:STAT?')
        if rp_s.rx_txt() == 'TD':
            break

    #time.sleep(0.18)
    #timenow = time.time()-start
    #outputfile.write(str(timenow))
    #outputfile.write(":\n")

    rp_s.tx_txt('ACQ:SOUR1:DATA?')
    buff_string = rp_s.rx_txt()
    buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
    buff = list(map(float, buff_string))
    #length =len(buff)
    buff_size = 12000
    #outputfile.write(str(buff))
    #outputfile.write("\n")

    #rp_s.tx_txt('ACQ:TPOS?')
    #trigLoc = int(rp_s.rx_txt())

   

    for i in range(buff_size-1):
        der=10*(buff[i+2]-buff[i])
        if(der<-0.005 and buff[i]>0.08):
            trig=0.08
        else:
            trig=0
        if(peak[0]==0):
            if(trig>0):
                peak[0]=1 
                peak_pos[0]=i
        else:
            if(peak[1]==0):
                if((i-peak_pos[0])>1500 and peak[1]==0 and trig>0):
                    peak[1]=1 
                    peak_pos[1]=i
            else:
                if(peak[2]==0):
                    if((i-peak_pos[1])>1500 and peak[2]==0 and trig>0):
                        peak[2]=1 
                        peak_pos[2]=i



    print(peak_pos[0], peak_pos[1], peak_pos[2])

    if (loop==1):
        break

    error[0]=peak_pos[0]-set_point[0]
    if(np.absolute(error[0])<300):
        k=0
        distance=peak_pos[2]-peak_pos[0]
        #error[0]=(float(peak_pos[k])-float(set_point[0]))/(float(distance))
        integral[k]+=error[0]
        Dc[k]=Pid(error[0],integral[k],Kp[k],Ki[k])
        Dc0=Dc[0]+0.9
        #rp_s.tx_txt('SOUR2:VOLT:OFFS ' +str(Dc[0]))
    
        rp_s.tx_txt('ANALOG:PIN AOUT0' + ','+str(Dc0))
        
    
    
        k=1
    
        relative_pos_set[k-1]=float(set_point[k])/float(distance)
        relative_pos_peak[k-1]=float(peak_pos[k]-peak_pos[0])/(float(distance))
        error[k]=relative_pos_peak[k-1]-relative_pos_set[k-1]
        integral[k]+=error[k]
        Dc[k]=Pid(error[k],integral[k],Kp[k],Ki[k])
        rp_s.tx_txt('SOUR1:VOLT:OFFS ' +str(Dc[1]))
        #if(error[0]>200 or error[0]<-200):
            #plot.plot(buff)
      
        actual = time.time()-start
        #print("Count", run, "Time: ", actual, peak_pos[0], Dc[0])
        #plot.figure()
        #plot.plot(buff)
        #plot.savefig('figs' +str(run))
        firstpeak.append(peak_pos[0])
        secondpeak.append(peak_pos[1])
        #triggerlocation.append(trigLoc)
        xpeak.append(actual)
    #print("ANALOG OUTPUT: ", rp_s.tx_txt('ANALOG:PIN? AOUT0'))
    else:
        print("........Cavity Drifting........")

    actual = time.time()-start
    run = run+1
    print("Count", run, "Time: ", actual, peak_pos[0], peak_pos[1], Dc[0], Dc[1])
    
    '''k=0
    distance=peak_pos[2]-peak_pos[0]
    #error[0]=(float(peak_pos[k])-float(set_point[0]))/(float(distance))
    error[0]=peak_pos[k]-set_point[0]
    integral[k]+=error[0]
    Dc[k]=Pid(error[0],integral[k],Kp[k],Ki[k])
    Dc0=Dc[0]+0.9
    #rp_s.tx_txt('SOUR2:VOLT:OFFS ' +str(Dc[0]))
    
    rp_s.tx_txt('ANALOG:PIN AOUT0' + ','+str(Dc0))
    
    
    k=1
    
    relative_pos_set[k-1]=float(set_point[k])/float(distance)
    relative_pos_peak[k-1]=(float(peak_pos[k])-float(peak_pos[0]))/(float(distance))
    error[k]=relative_pos_peak[k-1]-relative_pos_set[k-1]
    integral[k]+=error[k]
    Dc[k]=Pid(error[k],integral[k],Kp[k],Ki[k])
    rp_s.tx_txt('SOUR1:VOLT:OFFS ' +str(Dc[1]))
    
   

    run = run+1
    actual = time.time()-start
    print("Count", run, "Time: ", actual, peak_pos[0], peak_pos[1], Dc[0], Dc[1])
    #print("Count", run, "Time: ", actual, peak_pos[0], Dc[0])

    firstpeak.append(peak_pos[0])
    secondpeak.append(peak_pos[1])
    #triggerlocation.append(trigLoc)
    xpeak.append(actual)'''

    peak_pos[0]=peak_pos[1]=0
    peak[0]=peak[1]=peak[2]=peak[3]=0
    
    if(actual>3600):
        break

    #BREAKING OPTION
    if(Dc[0]<-1 or Dc[0]>1):
        print("dc0 out of range")
        break
    if(Dc[1]<-1 or Dc[1]>1):
        print("dc1 out of range")
        break

  
#outputfile.close()

#plot.savefig('allplots')
#print("final: ", peak_pos[0], peak_pos[1], peak_pos[2])
print("Executed Successfully")
#print("Executed Successfully & loop = ", loop, " Dc[0] = ", Dc[0])

dat=np.array([xpeak, firstpeak, secondpeak])
dat = dat.T
np.savetxt('data.txt', dat)

#with open("file.txt", "w") as output:
    #output.write(str(buff))

#print("length=", length)

plot.plot(buff)

fig, (ax1, ax2) = plot.subplots(2)        
ax1.plot(xpeak, firstpeak, color='green', label='First Peak (Clock Laser)')
ax2.plot(xpeak, secondpeak, color='blue', label='679 Laser Peak')
#ax3.plot(xpeak, triggerlocation, color='olive', label='Trigger Position')


plot.ylabel('Peak Positions')
plot.xlabel('Time Elapsed in seconds')
ax1.axhline(2000, color='r', linestyle='-', lw=1, label='First Peak Lock Position')
ax2.axhline(6000, color='m', linestyle='-', lw=1, label='679 Lock Position')
#ax3.axhline(0, color='c', linestyle='-', lw=1, label='Trigger 0 Position')
#ax2.text(400, 2500, 'Peak width = 400 = 0.4 ms = 30 MHz', fontsize = 10, color='green', bbox=dict(facecolor='none', edgecolor='green', boxstyle='round'))
ax1.legend()
ax2.legend()
#ax3.legend()
fig.suptitle("Laser Locking with Time", fontsize = 16)
#plot.ylabel('Voltage')
#plot.xlabel('Samples with Decimation Factor of 128')

#plot.savefig('my_plot_ext.png')
print("Executed Successfully")
plot.show()
