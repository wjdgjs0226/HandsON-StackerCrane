#!/usr/bin/env python3
from ev3dev2.display import Display
from ev3dev2.sound import Sound
from ev3dev2.motor import LargeMotor
from ev3dev2.motor import MediumMotor
from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.motor import SpeedDPS, SpeedRPM, SpeedRPS, SpeedDPM
from ev3dev2.motor import MoveTank
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3, INPUT_4
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor.lego import TouchSensor
from time import sleep, time
from multiprocessing import Process
import datetime
import traceback
import math
import json
import socket
import threading
import sys

# SRC for Crane1 (Starting from Input Point)
# Based on EV3DEV, Python 3.7.3
# Last Update: 20190817


# Function to test socket function of EV3Dev
# Test this function only when the EV3Dev is connected to an Android Mobile Phone using BlueTooth or port-forwarded Wifi network
def funTestSocket():
    global lcd, sock
    global gintLastCommand, gintTotalCommand, glstCommand, bolReConnect
    global MTY, M1IO, LM1X, CS, CS2
    global xcf, xcc

    # Initial position of the Crane
    # X Position: Origin Point A
    xcc = 0
    # Y Position: Init Position
    ycc = -1

    # The following code set the ip address and port of the socket server
    # If you connect the EV3 to the internet using Mobile Phone network via bluetooth, you should replace the ip address with the dns or your socket server,
    HOST, PORT = "192.168.0.4", 8513
    # HOST, PORT = "192.168.0.4", 8513

    # Try a connection to a server
    try:
        bolProgramEnd = False
        bolReConnect = False

        while not bolProgramEnd:

            # First Time Display is Slow, so display First
            lcd.clear()
            lcd.draw.text((10,5),  'Connecting to Server ...')
            lcd.update()

            # Connect to server
            try:
                # Create a socket (SOCK_STREAM means a TCP socket)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(80)
                sock.connect((HOST, PORT))
                sock.settimeout(None)
                # To avoid the EV3 Brick stops at sock.recv (here we use blocking mode),
                # Here we start the sock.recv in another thread
                client_thread = threading.Thread(target=StartClientReceive)
                client_thread.daemon = True
                client_thread.start()

            except socket.timeout:
                # Here unable to connect server, may be the connection is permanently lost
                # Exit app, fix connection problem and run client again!!!
                # The Connection problem can be solved by - 
                # Wifi reconnection (After deleting (Wireless and Networks -> Wifi -> enter the connected network -> forget -> Reboot)
                sys.exit()

            try:
                # Login
                # Here assume sock.send will be ok for the first time, otherwise program stops here
                # ********** PROGRAM MIGHT STOP AT THE FOLLOWING CODES, WE DEAL WITH THIS LATER ********
                lcd.clear()
                lcd.draw.text((10,5),  'Before Send Login')
                lcd.update()
                sleep(1)
                
                sock.sendall(":Login".encode())

                # Initialize Movetank motors (Y axis)
                MTY.on_for_degrees(0,0,0, brake = False)
                while not MTY.is_overloaded:
                    MTY.on(-30,-30)
                sleep(0.1)
                MTY.on_for_degrees(80,80,0.01, brake = True)

                # In this moment, we let the server to change the Null value true so that the Server can send a command
                sock.sendall(":Finished1".encode())

                # Display after message is sent to the server
                lcd.clear()
                lcd.draw.text((10,5),  'After Login Sent')
                lcd.update()

                # ********** PROGRAM MIGHT STOP ends here if the connection error occurs **********
            except:
                # Display Login has failed
                lcd.clear()
                lcd.draw.text((10,5),  'Login Failed, Exiting')
                lcd.update()
                sys.exit()

            bolEnd = False
 
            while not bolEnd:
                # Check if socket is disconnected
                if bolReConnect:
                    sock.close
                    bolEnd = True
                else:
                    # Check if new command arrived from server
                    # When the value of gintTotalCommand is greater than gintLastCommand, we consider the new command is sent from the server
                    if gintLastCommand < gintTotalCommand:
                        gintLastCommand += 1

                        # Update the list which stores received commands in a sequence
                        received = glstCommand[gintLastCommand-1]

                        # If server commands to disconnect
                        if received == ":Disconnect":
                            # Change the boolean value and break the loop
                            bolEnd = True
                        
                        # LoginOK - notify the connection is established properly 
                        elif received == ":LoginOK":
                            
                            sound.beep()
                            lcd.clear()
                            lcd.draw.text((10,5),  'Server Connected')
                            lcd.update()
                            
                        # When the normal command arrives
                        elif len(received) == 4:

                            # Set a new coordinate and check another stocker's position
                            # Change the Chr to Number
                            INOUT = received[0]
                            LEFTRIGHT = received[1]
                            xcf = ord(received[2])-65
                            ycf = ord(received[3])-65
                            
                            # If the crane has to go to the input point
                            if xcf == 1:
                                Posmove(xcf,xcc,ycf,ycc)
                                sock.sendall(":Readyforload".encode())
                                sleep(4)
                                Midmotormove(INOUT,LEFTRIGHT,xcf,ycf)
                                xcc = 1
                                ycc=-1
                            # If the crane has to go to the output point
                            elif xcf == 20:
                                Posmove(xcf,xcc,ycf,ycc)
                                Midmotormove(INOUT,LEFTRIGHT,xcf,ycf)
                                xcc = 20
                                ycc = -1
                            # If the crane has to go to the origin point V
                            elif xcf == 21:
                                Posmove(xcf,xcc,ycf,ycc)
                                xcc = 21
                                ycc = -1
                            # If the crane has to go to the origin point A
                            elif xcf == 0:
                                Posmove(xcf,xcc,ycf,ycc)
                                xcc = 0
                                ycc = -1
                            # Other general cases
                            else:
                                Posmove(xcf,xcc,ycf,ycc)
                                Midmotormove(INOUT,LEFTRIGHT,xcf,ycf)
                                xcc=xcf
                                if ycf == 0:
                                    ycc = -1
                                else:
                                    ycc=ycf
                            sleep(0.1)
                            # Tell the server the task is finished
                            sock.sendall(":Finished1".encode())
                        
                        # When the command which requires to move out
                        elif len(received) == 2:
                            
                            # Only involves x coordinate change (Moving away)
                            # Move to the point (received position - 4)
                            # It allows the other crane to do the task without collision
                            xcf = ord(received[1])-69
                            # When the crane has to move to the origin point to avoid
                            if xcf <= 1:
                                xcf = 0
                            else:
                                pass
                            xmove(xcf, xcc)
                            xcc=xcf
                            sleep(0.1)
                            # Tell the server the task is finished
                            sock.sendall(":Finished1".encode())

                        # Emergency Stop (Each Crane moves to each origin point) Crane1 - A / Crane2 - V)
                        elif len(received) == 3:

                            # Emergency Exit
                            # Move to the origin point A
                            xcf = 0
                            xmove(xcf,xcc)
                            sleep(0.1)
                            sys.exit()

                        else:
                            pass
                sleep(0.01)

            if not bolReConnect:
                # Tell the server to close connection and wait for another client
                data = ":End"
                try:
                    sock.sendall(data.encode())
                except:
                    pass
                sock.close

                # Disconnected Normally by server, so client end program
                bolProgramEnd = True
            else:
                bolReConnect = False
    finally:
        pass

# Function to receive data from Socket Server, this function is to be started in another thread
def StartClientReceive():
    global sock, gintTotalCommand, glstCommand, bolReConnect, MTY

    bolEnd = False

    while not bolEnd:
        # Receive Data From Server and store it inside the list glstCommand
        received = str(sock.recv(1024).decode())

        if received == "":
            # Socket disconnected, may be due to mobile phone connection lost
            # There are 2 situations to determine whether the connection is lost
            # 1. received = ""
            # 2. We need to use the heartbit technique, if there is no response from the socket server for a particular time, say 5 seconds, then the connectio is assumed to be lost
            # The following codes deal with situation 1
            bolEnd = True
            bolReConnect = True

        elif received == ":LoginOK":
            
            # Beep a sound when the connection is established
            sound.beep()
            lcd.clear()
            lcd.draw.text((10,5),  'Server Connected')
            lcd.update()

        else:
            # Normal Receive
            gintTotalCommand += 1
            glstCommand.append(received)

            if received == ":Disconnect":
                bolEnd = True

# Function to move the lift of the stocker & position of the Crane simultaneously
def Posmove(xf,xc,yf,yi):

    c = yf-yi

    # Load/Out/Origins
    if xf == 1 or xf == 20 or xf == 21 or xf == 0:
        Xmove = Process(target = xmove, args = (xf,xc))
        Xmove.start()
        
        while not MTY.is_overloaded:
            MTY.on(-30,-30)
        sleep(0.1)
        MTY.on_for_degrees(50,50,0.01, brake = True)
        Xmove.join()

    else:
        # MoveTank Initialization (When the lastest task was done at y = 0 (1st floor))
        if yi == -1:
            Xmove = Process(target = xmove, args = (xf,xc))
            Xmove.start()
            MTY.on_for_rotations(50,50,(2*(c-1))+0.4, brake = True)
            Xmove.join()
        # Other cases
        else:
            Xmove = Process(target = xmove, args = (xf,xc))
            Xmove.start()
            MTY.on_for_rotations(50,50,2*c, brake = True)
            Xmove.join()

# Function to move Medium Motor
def Midmotormove(inout, leftright, xf, yf): 
    
    # Input 
    if xf == 1:
        M1IO.on_for_rotations(50, -1.45,brake=True)
        sleep(0.5)
        MTY.on_for_rotations(30,30,0.42,brake=True)
        sleep(0.5)
        M1IO.on_for_rotations(50, 1.45,brake=True)
        sleep(0.5)
        MTY.on_for_rotations(30,30,-0.42,brake=True)
        sleep(0.5)
    # Output
    elif xf == 20:
        MTY.on_for_degrees(30,30,90,brake=True)
        sleep(0.5)
        M1IO.on_for_rotations(50, -1.45,brake=True)
        sleep(0.5)
        MTY.on_for_degrees(30,30,-90,brake=True)
        sleep(0.5)
        M1IO.on_for_rotations(50, 1.45,brake=True)
        sleep(0.5)
    # Origin points - Midmotor does not need to move
    elif xf == 0:
        pass
    elif xf == 21:
        pass

    # Other typical tasks
    else:
        if inout == "B":
            if leftright == "B":
                M1IO.on_for_rotations(50, 1.45,brake=True)
                sleep(0.5)
                MTY.on_for_rotations(-30,-30,0.3,brake=True)
                sleep(0.5)
                M1IO.on_for_rotations(50, -1.45,brake=True)
                sleep(0.5)
                MTY.on_for_rotations(30,30,0.3,brake=True)
                sleep(0.5)
                if yf == 0:
                    MTY.on_for_degrees(0,0,0, brake = False)
                    while not MTY.is_overloaded:
                        MTY.on(-30,-30)
                    sleep(0.1)
                    MTY.on_for_degrees(50,50,0.01, brake = True)
                else:
                    pass

            else:
                M1IO.on_for_rotations(50,-1.45,brake=True)
                sleep(0.5)
                MTY.on_for_rotations(-30,-30,0.3,brake=True)
                sleep(0.5)
                M1IO.on_for_rotations(50,1.45,brake=True)
                sleep(0.5)
                MTY.on_for_rotations(30,30,0.3,brake=True)
                sleep(0.5)
                if yf == 0:
                    MTY.on_for_degrees(0,0,0, brake = False)
                    while not MTY.is_overloaded:
                        MTY.on(-30,-30)
                    sleep(0.1)
                    MTY.on_for_degrees(50,50,0.01, brake = True)
                else:
                    pass
        else:
            if leftright == "B":
                MTY.on_for_rotations(-30,-30,0.3,brake=True)
                sleep(0.5)
                M1IO.on_for_rotations(50,1.45,brake=True)
                sleep(0.5)
                MTY.on_for_rotations(30,30,0.3,brake=True)
                sleep(0.5)
                M1IO.on_for_rotations(50,-1.45,brake=True)
                sleep(0.5)
                if yf == 0:
                    MTY.on_for_degrees(0,0,0, brake = False)
                    while not MTY.is_overloaded:
                        MTY.on(-30,-30)
                    sleep(0.1)
                    MTY.on_for_degrees(50,50,0.01, brake = True)
                else:
                    pass
            else:
                MTY.on_for_rotations(-30,-30,0.3,brake=True)
                sleep(0.5)
                M1IO.on_for_rotations(50,-1.45,brake=True)
                sleep(0.5)
                MTY.on_for_rotations(30,30,0.3,brake=True)
                sleep(0.5)
                M1IO.on_for_rotations(50,1.45,brake=True)
                sleep(0.5)
                if yf == 0:
                    MTY.on_for_degrees(0,0,0, brake = False)
                    while not MTY.is_overloaded:
                        MTY.on(-30,-30)
                    sleep(0.1)
                    MTY.on_for_degrees(50,50,0.01, brake = True)
                else:
                    pass

# Function to operate Crane's X motor
def xmove(xf, xc):
    global MTY, M1IO, LM1X, CS

    aim = xf-xc
    bangle = 230

    # When the crane has to go to A
    if xf == 0:
        # When it moves from B to A
        if xc == 1:
            for i in range(1,51):
                LM1X.on(-i, brake = False)
                sleep(0.00001)

            for i in range(10,56):
                LM1X.on(-60+i, brake = True)
                sleep(0.00001)
            Move = True
            while Move:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move = False
            else:
                LM1X.off(brake = True)
           
        # When it stays
        elif xc == 0:
            pass
        # If it moves from C to A
        elif xc == 2:
            for i in range(1,51):
                LM1X.on(-i, brake = False)
                
            LM1X.on_for_degrees(-50, bangle, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake = True)
        
            Move1 = True
            while Move1:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move1 = False
            else:
                LM1X.off(brake = True)
                 
        # If it moves from D to A
        elif xc == 3:
            for i in range(1,51):
                LM1X.on(-i, brake = False)

            LM1X.on_for_degrees(-50, bangle + 200, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake = True)
        
            Move40 = True
            while Move40:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move40 = False
            else:
                LM1X.off(brake = True)
            sleep(0.1)
        # If it moves from U to A
        elif xc == 20:
            for i in range(1, 51):
                LM1X.on(-i, brake = False)
        
            LM1X.on_for_degrees(50, -120, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake=True)
            
            Move60 = True
            while Move60:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move60 = False
            else:
                LM1X.off(brake = True)

            for i in range(1, 51):
                LM1X.on(-i, brake = False)
        
            LM1X.on_for_degrees(50, (aim+5)*bangle + 30, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake=True)

            Move65 = True
            while Move65:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move65 = False
            else:
                LM1X.off(brake = True)
            
            for i in range(1,51):
                LM1X.on(-i, brake = False)
            
            LM1X.on_for_degrees(50,-400,brake=True)
                
            for i in range(10,56):
                LM1X.on(-60+i, brake = True)

            Move70 = True
            while Move70:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move70 = False
            else:
                LM1X.off(brake = True)
        # If it moves from V to A
        elif xc == 21:
            for i in range(1, 51):
                LM1X.on(-i, brake = False)

            LM1X.on_for_degrees(50, -540, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake=True)
            
            Move75 = True
            while Move75:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move75 = False
            else:
                LM1X.off(brake = True)

            for i in range(1, 51):
                LM1X.on(-i, brake = False)
        
            LM1X.on_for_degrees(50, (aim+6)*bangle + 30, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake=True)

            Move80 = True
            while Move80:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move80 = False
            else:
                LM1X.off(brake = True)
            
            for i in range(1,51):
                LM1X.on(-i, brake = False)
            
            LM1X.on_for_degrees(50,-400,brake=True)
                
            for i in range(10,56):
                LM1X.on(-60+i, brake = True)
            
            Move85 = True
            while Move85:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move85 = False
            else:
                LM1X.off(brake = True)
        # Other Cases
        else:
            for i in range(1,51):
                LM1X.on(-i, brake = False)

            LM1X.on_for_degrees(50, (aim+3)*bangle + 30, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake = True)
        
            Move2 = True
            while Move2:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move2 = False
            else:
                LM1X.off(brake = True)
            sleep(0.1)

            for i in range(1,51):
                LM1X.on(-i, brake = False)
            
            LM1X.on_for_degrees(50,-400,brake=True)
                
            for i in range(10,56):
                LM1X.on(-60+i, brake = True)
        
            Move3 = True
            while Move3:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move3 = False
            else:
                LM1X.off(brake = True)

    # When The crane has to go to B
    elif xf == 1:
        # When it moves from C to B
        if xc == 2:  
            LM1X.on_for_degrees(-20,20,brake=True)

            Move4 = True
            while Move4:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move4 = False
            else:
                LM1X.off(brake = True)
        # When it stays
        elif xc == 1:
            pass
        # When it moves from A to B
        elif xc == 0:
            for i in range(1, 51):
                LM1X.on(i, brake = False)
        
            LM1X.on_for_degrees(50, 400, brake=True)
            for i in range(10,56):
                LM1X.on(60-i, brake=True)

            Move5 = True
            while Move5:
                LM1X.on(5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move5 = False
            else:
                LM1X.off(brake = True)
        # When it moves from D to B
        elif xc == 3:
            for i in range(1,41):
                LM1X.on(-i, brake = False)

            for i in range(20,56):
                LM1X.on(-60+i, brake = True)
        
            Move40 = True
            while Move40:
                LM1X.on(-5)
                if CS2.is_released:
                    sleep(Sensor_wait)
                    Move40 = False
            else:
                LM1X.off(brake = True)
            
            LM1X.on_for_degrees(-20,20,brake=True)

            Move50 = True
            while Move50:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move50 = False
            else:
                LM1X.off(brake = True)
        # When it moves from U to B
        elif xc == 20:
            for i in range(1, 51):
                LM1X.on(-i, brake = False)
        
            LM1X.on_for_degrees(50, -100, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake=True)
            
            Move90 = True
            while Move90:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move90 = False
            else:
                LM1X.off(brake = True)

            for i in range(1, 51):
                LM1X.on(-i, brake = False)
        
            LM1X.on_for_degrees(50, (aim+4)*bangle + 140, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake=True)

            Move95 = True
            while Move95:
                LM1X.on(-5)
                if CS2.is_released:
                    sleep(Sensor_wait)
                    Move95 = False
            else:
                LM1X.off(brake = True)
            
            LM1X.on_for_degrees(-20,20,brake=True)

            Move100 = True
            while Move100:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move100 = False
            else:
                LM1X.off(brake = True)
        # When it moves from V to B
        elif xc == 21:
            for i in range(1, 51):
                LM1X.on(-i, brake = False)

            LM1X.on_for_degrees(50, -540, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake=True)
            
            Move105 = True
            while Move105:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move105 = False
            else:
                LM1X.off(brake = True)

            for i in range(1, 51):
                LM1X.on(-i, brake = False)
        
            LM1X.on_for_degrees(50, (aim+5)*bangle + 140, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake=True)

            Move110 = True
            while Move110:
                LM1X.on(-5)
                if CS2.is_released:
                    sleep(Sensor_wait)
                    Move110 = False
            else:
                LM1X.off(brake = True)

            LM1X.on_for_degrees(-20,20,brake=True)

            Move115 = True
            while Move115:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move115 = False
            else:
                LM1X.off(brake = True)
        # Other cases
        else:
            for i in range(1,51):
                    LM1X.on(-i, brake = False)
            if xc > 4:
                LM1X.on_for_degrees(50, (aim+2)*bangle + 140, brake=True)   # + 40
            else:
                LM1X.on_for_degrees(50, (aim+2)*bangle + 120, brake=True)   # + 40
            for i in range(10,56):
                LM1X.on(-60+i, brake = True)
        
            Move6 = True
            while Move6:
                LM1X.on(-5)
                if CS2.is_released:
                    sleep(Sensor_wait)
                    Move6 = False
            else:
                LM1X.off(brake = True)

            LM1X.on_for_degrees(-20,20,brake=True)
            Move7 = True

            while Move7:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move7 = False
            else:
                LM1X.off(brake = True)
    # When the crane has to go to U
    elif xf == 20:
        # When it moves from V to U
        if xc == 21:
            for i in range(1,51):
                LM1X.on(-i, brake = False)
                
            for i in range(10,56):
                LM1X.on(-60+i, brake = True)
        
            Move21 = True
            while Move21:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move21 = False
            else:
                LM1X.off(brake = True)
                sleep(0.5)
        # When it moves from T to U
        elif xc == 19:
            Move140 = True
            while Move140:
                LM1X.on(5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move140 = False
                else:
                    LM1X.off(brake = True)
        # When it moves from S to U
        elif xc == 18:
            for i in range(1,41):
                LM1X.on(i, brake = True)
                sleep(0.00001)
            for i in range(20,56):
                LM1X.on(60-i, brake = True)
                sleep(0.00001)
            Move170 = True
            while Move170:
                LM1X.on(5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move170 = False
            else:
                LM1X.off(brake = True)
        # Stays at same location
        elif xc == 20:
            pass
        # Other Cases
        else:
            for i in range(1, 51):
                LM1X.on(i, brake = False)
        
            LM1X.on_for_degrees(50, (aim-2)*bangle - 10, brake=True)
            for i in range(10,56):
                LM1X.on(60-i, brake=True)

            Move18 = True
            while Move18:
                LM1X.on(5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move18 = False
            else:
                LM1X.off(brake = True)

    # When the Crane has to go to V
    elif xf == 21:
        # When it moves from U to V
        if xc == 20:
            for i in range(1, 51):
                    LM1X.on(i, brake = False)
            
            for i in range(10,56):
                LM1X.on(60-i, brake=True)
            
            Move25 = True
            while Move25:
                LM1X.on(5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move25 = False
            else:
                LM1X.off(brake = True)
        # When it moves from T to V
        elif xc == 19:
            for i in range(1, 51):
                LM1X.on(i, brake = False)
            
            for i in range(10,56):
                LM1X.on(60-i, brake=True)
                
            Move300 = True
            while Move300:
                LM1X.on(5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move300 = False
            else:
                LM1X.off(brake = True)
                sleep(0.5)
        # Stays at same location
        elif xc == 21:
            pass
        # Other cases
        else:
            for i in range(1, 51):
                LM1X.on(i, brake = False)

            LM1X.on_for_degrees(50, (aim-1)*bangle - 40, brake=True)
            for i in range(10,56):
                LM1X.on(60-i, brake=True)
            
            Move30 = True
            while Move30:
                LM1X.on(5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move30 = False
            else:
                LM1X.off(brake = True)

    # When the crane has to go to T
    elif xf == 19:
        # When it moves from A to T
        if xc == 0:
            for i in range(1, 51):
                LM1X.on(i, brake = False)
        
            LM1X.on_for_degrees(50, 540, brake=True)
            for i in range(10,56):
                LM1X.on(60-i, brake=True)
            
            Move900 = True
            while Move900:
                LM1X.on(5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move900 = False
            else:
                LM1X.off(brake = True)
            
            for i in range(1, 51):
                LM1X.on(i, brake = False)
        
            LM1X.on_for_degrees(50, (aim-3)*bangle - 40, brake=True)
            for i in range(10,56):
                LM1X.on(60-i, brake=True)

            Move1000 = True
            while Move1000:
                LM1X.on(5)
                while not CS2.is_released:
                    LM1X.on(5)
                    sleep(Sensor_wait)
            else:
                LM1X.off(brake = True)
        # When it moves from B to T
        elif xc == 1:
            LM1X.on_for_degrees(10,10,brake = True)
            Move1200 = True
            while Move1200:
                LM1X.on(5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move1200 = False
            else:
                LM1X.off(brake = True)
                sleep(0.5)

            for i in range(1, 51):
                LM1X.on(i, brake = False)
        
            LM1X.on_for_degrees(50, (aim-2)*bangle - 40, brake=True)
            for i in range(10,56):
                LM1X.on(60-i, brake=True)

            Move1300 = True
            while Move1300:
                LM1X.on(5)
                if CS2.is_released:
                    sleep(Sensor_wait)
                    Move1300 = False
            else:
                LM1X.off(brake = True)
        # When it moves from U to T
        elif xc == 20:
            Move120 = True
            while Move120:
                LM1X.on(-5, brake = True)
                if CS2.is_released:
                    sleep(Sensor_wait)
                    Move120 = False
            else:
                LM1X.off(brake = True)
        # When it moves from V to T
        elif xc == 21:
            Move115 = True
            while Move115:
                LM1X.on(-5, brake = True)
                if CS2.is_released:
                    sleep(Sensor_wait)
                    Move115 = False
            else:
                LM1X.off(brake = True)
        # When it moves from S to T
        elif xc == 18:
            for i in range(1, 41):
                    LM1X.on(i, brake = False)

            for i in range(20,56):
                LM1X.on(60-i, brake=True)
            Move130 = True
            while Move130:
                LM1X.on(5)
                if CS2.is_released:
                    sleep(Sensor_wait)
                    Move130 = False
            else:
                LM1X.off(brake = True)
        # Stays at same location
        elif xc == 19:
            pass
        # Other Cases
        else:
            for i in range(1, 51):
                    LM1X.on(i, brake = False)

            LM1X.on_for_degrees(50, (aim-1)*bangle - 40, brake=True)
            for i in range(10,56):
                LM1X.on(60-i, brake=True)
            
            Move132 = True
            while Move132:
                LM1X.on(5)
                if CS2.is_released:
                    sleep(Sensor_wait)
                    Move132 = False
            else:
                LM1X.off(brake = True)

    # Whole Other Cases
    else:
        # When the crane starts from A
        if xc == 0:
            sleep(2)
            # When the crane moves from A to C
            if xf == 2:
                for i in range(1, 51):
                    LM1X.on(i, brake = False)
            
                LM1X.on_for_degrees(50, 540, brake=True)
                for i in range(10,56):
                    LM1X.on(60-i, brake=True)
                
                Move8 = True
                while Move8:
                    LM1X.on(5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move8 = False
                else:
                    LM1X.off(brake = True)
            # When the crane moves from A to any place other than B and C
            else:
                for i in range(1, 51):
                    LM1X.on(i, brake = False)
            
                LM1X.on_for_degrees(50, 540, brake=True)
                for i in range(10,56):
                    LM1X.on(60-i, brake=True)
                
                Move9 = True
                while Move9:
                    LM1X.on(5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move9 = False
                else:
                    LM1X.off(brake = True)

                for i in range(1, 51):
                    LM1X.on(i, brake = False)
            
                LM1X.on_for_degrees(50, (aim-3)*bangle - 40, brake=True)
                for i in range(10,56):
                    LM1X.on(60-i, brake=True)

                Move10 = True
                while Move10:
                    LM1X.on(5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move10 = False
                else:
                    LM1X.off(brake = True)
        # When the crane starts from B
        elif xc == 1:
            # When the crane moves from B to C
            if xf == 2:
                LM1X.on_for_degrees(10,20,brake = True)
                Move11 = True
                while Move11:
                    LM1X.on(5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move11 = False
                else:
                    LM1X.off(brake = True)
            # When the crane moves from B to any place other than C and A
            else:
                LM1X.on_for_degrees(10,20,brake = True)
                Move12 = True
                while Move12:
                    LM1X.on(5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move12 = False
                else:
                    LM1X.off(brake = True)
                    sleep(0.5)

                for i in range(1, 51):
                    LM1X.on(i, brake = False)
            
                LM1X.on_for_degrees(50, (aim-2)*bangle + 40, brake=True)
                for i in range(10,56):
                    LM1X.on(60-i, brake=True)

                Move13 = True
                while Move13:
                    LM1X.on(5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move13 = False
                else:
                    LM1X.off(brake = True)
        # When the crane starts from U
        elif xc == 20:
            # When it moves from U to S
            if xf == 18:
                for i in range(1, 51):
                    LM1X.on(-i, brake = False)
            
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)
                
                Move150 = True
                while Move150:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move150 = False
                else:
                    LM1X.off(brake = True)
            # When it moves from U to R
            elif xf == 17:
                for i in range(1, 51):
                    LM1X.on(-i, brake = False)
            
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)
                
                Move190 = True
                while Move190:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move190 = False
                else:
                    LM1X.off(brake = True)

                for i in range(1, 41):
                    LM1X.on(-i, brake = False)
            
                for i in range(20,56):
                    LM1X.on(-60+i, brake=True)

                Move200 = True
                while Move200:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move200 = False
                else:
                    LM1X.off(brake = True)
            # When it moves from U to H
            elif xf == 7:
                for i in range(1, 51):
                    LM1X.on(-i, brake = False)
            
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)
                Move19 = True
                while Move19:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move19 = False
                else:
                    LM1X.off(brake = True)

                for i in range(1, 51):
                    LM1X.on(-i, brake = False)
            
                LM1X.on_for_degrees(50, (aim+3)*bangle -40, brake=True)
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)

                Move20 = True
                while Move20:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move20 = False
                else:
                    LM1X.off(brake = True)
            # When it moves from U to I
            elif xf == 8:
                for i in range(1, 51):
                    LM1X.on(-i, brake = False)
            
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)
                
                Move19 = True
                while Move19:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move19 = False
                else:
                    LM1X.off(brake = True)

                for i in range(1, 51):
                    LM1X.on(-i, brake = False)
            
                LM1X.on_for_degrees(50, (aim+3)*bangle, brake=True)
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)

                Move20 = True
                while Move20:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move20 = False
                else:
                    LM1X.off(brake = True)
            # Other Cases
            else:
                for i in range(1, 51):
                    LM1X.on(-i, brake = False)
            
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)
                
                Move19 = True
                while Move19:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move19 = False
                else:
                    LM1X.off(brake = True)

                for i in range(1, 51):
                    LM1X.on(-i, brake = False)
            
                LM1X.on_for_degrees(50, (aim+3)*bangle + 50, brake=True)
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)

                Move20 = True
                while Move20:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move20 = False
                else:
                    LM1X.off(brake = True)
        # When the Crane starts from V
        elif xc == 21:
            sleep(2)
            # When it moves from V to S
            if xf == 18:
                for i in range(1, 51):
                    LM1X.on(-i, brake = False)

                LM1X.on_for_degrees(50, -640, brake=True)
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)

                Move220 = True
                while Move220:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move220 = False
                else:
                    LM1X.off(brake = True)
            # When it moves from V to R
            elif xf == 17:
                for i in range(1, 51):
                    LM1X.on(-i, brake = False)

                LM1X.on_for_degrees(50, -640, brake=True)
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)

                Move220 = True
                while Move220:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move220 = False
                else:
                    LM1X.off(brake = True)
                
                for i in range(1, 41):
                    LM1X.on(-i, brake = False)
            
                for i in range(20,56):
                    LM1X.on(-60+i, brake=True)
                Move230 = True
                while Move230:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move230 = False
                else:
                    LM1X.off(brake = True)
            # Other Cases
            else:
                for i in range(1, 51):
                    LM1X.on(-i, brake = False)

                LM1X.on_for_degrees(50, -640, brake=True)
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)
                
                Move22 = True
                while Move22:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move22 = False
                else:
                    LM1X.off(brake = True)

                for i in range(1, 51):
                    LM1X.on(-i, brake = False)
            
                LM1X.on_for_degrees(50, (aim+4)*bangle + 40, brake=True)
                for i in range(10,56):
                    LM1X.on(-60+i, brake=True)

                Move23 = True
                while Move23:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move23 = False
                else:
                    LM1X.off(brake = True)
        # When it starts from T
        elif xc == 19:
            for i in range(1,51):
                LM1X.on(-i, brake = False)
                
            LM1X.on_for_degrees(50, (aim+1)*bangle + 40, brake=True)
            for i in range(10,56):
                LM1X.on(-60+i, brake = True)
        
            Move135 = True
            while Move135:
                LM1X.on(-5)
                if CS.is_released:
                    sleep(Sensor_wait)
                    Move135 = False
            else:
                LM1X.off(brake = True)
                sleep(0.5)

        # Other Cases
        else:
            if aim < -1:
                for i in range(1,51):
                    LM1X.on(-i, brake = False)
                    
                LM1X.on_for_degrees(50, (aim+1)*bangle + 40, brake=True)
                for i in range(10,56):
                    LM1X.on(-60+i, brake = True)
            
                Move15 = True
                while Move15:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move15 = False
                else:
                    LM1X.off(brake = True)
                    sleep(0.5)

            elif aim == -1:
                for i in range(1,41):
                    LM1X.on(-i, brake = True)
                    sleep(0.00001)
                for i in range(20,56):
                    LM1X.on(-60+i, brake = True)
                    sleep(0.00001)
                Move16 = True
                while Move16:
                    LM1X.on(-5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move16 = False
                else:
                    LM1X.off(brake = True)

            elif aim == 1:
                for i in range(1,41):
                    LM1X.on(i, brake = True)
                    sleep(0.00001)
                for i in range(20,56):
                    LM1X.on(60-i, brake = True)
                    sleep(0.00001)
                Move17 = True
                while Move17:
                    LM1X.on(5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move17 = False
                else:
                    LM1X.off(brake = True)
                
            elif aim == 0:
                pass

            else:
                for i in range(1, 51):
                    LM1X.on(i, brake = False)
            
                LM1X.on_for_degrees(50, (aim-1)*bangle - 40, brake=True)
                for i in range(10,56):
                    LM1X.on(60-i, brake=True)

                Move18 = True
                while Move18:
                    LM1X.on(5)
                    if CS.is_released:
                        sleep(Sensor_wait)
                        Move18 = False
                else:
                    LM1X.off(brake = True)
                
# The Main program starts here ***********************************************************************************

try:
    # Create Global Variables
    
    # gintLastCommand is the last command number already processed
    gintLastCommand = 0

    # gintTotalCommand is the total number of command received from the socket server
    gintTotalCommand = 0

    # Create List storing all commands received from socket server
    glstCommand = []

    #Motors and Sensors
    lcd = Display()
    sound = Sound()
    LM1X = LargeMotor(OUTPUT_A)
    M1IO = MediumMotor(OUTPUT_B)
    MTY = MoveTank(OUTPUT_C, OUTPUT_D)
    CS = TouchSensor(INPUT_1)
    CS2 = TouchSensor(INPUT_2)
  

    # Start Main Program
    funTestSocket()
except:
    # If there is any error, it will be stored in the log file in the same directory
    pass

# End Of Pard F - This is the end of the program ****************************************************************************
