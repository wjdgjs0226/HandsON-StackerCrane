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
from time import sleep, time
from multiprocessing import Process
import datetime
import traceback
import math
import json
import socket
import threading
import sys

# Function to run the input device of AutoFactory
def funTestSocket():
    '''Begins to run the input device and establish connection between Server'''
    global lcd, sock
    global gintLastCommand, gintTotalCommand, glstCommand, bolReConnect
    global MMTY, MM1, LMC, CS1, CS2, CS4
    global Release

    # Initial position of the trailer
    xcc = 0
    ycc = -1

    # Initialize the release bool value
    # It identifies whether the input has loaded a cartridge
    Release = False

    # The following code set the ip address and port of the socket server
    # If you connect the EV3 to the internet using Mobile Phone network via bluetooth, you should replace the ip address with the dns or your socket server,
    HOST, PORT = " ", 8515
    # HOST, PORT = "*USE THE IP ADDRESS", 8515

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
                # Exit app, fix connection problem and run client again
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

                lcd.clear()
                lcd.draw.text((10,5),  'After Login Sent')
                lcd.update()

                # ********** PROGRAM MIGHT STOP ends here **********
            except:
                # Display Login Successful
                lcd.clear()
                lcd.draw.text((10,5),  'Login Failed, Exiting')
                lcd.update()
                sys.exit()

            bolEnd = False
            while not bolEnd:
                if CS1.reflected_light_intensity > 10:
                    sound.beep()
                    MMC.on(15, brake = False)
                    Op = True
                    while Op:
                        if CS2.reflected_light_intensity > 25:
                            MMC.off()
                            MMTY.on(-30, -30)
                            Op = True
                            while Op:
                                if CS4.reflected_light_intensity > 30:
                                    MMTY.off(brake = True)
                                    Op = False
                                else:
                                    pass
                            MMTY.on_for_degrees(30, 30, 530, brake=True)
                            proc = Process(target = MMT)
                            proc.start()
                            MMC.on_for_seconds(15,5,brake=False)
                            sock.sendall(":Finished3".encode())
                            op = True
                            while op:
                                if Release == True:
                                    MMTY.on_for_degrees(40, 40, -520, brake=True)
                                    sleep(5)
                                    Release = False
                                    op = False
                                else:
                                    sleep(1)
                            else:
                                sleep(1)
                        else:
                            sleep(0.01)
                    else:
                        sleep(0.01)
                else:
                    sleep(1)
                # Check if socket is disconnected
                if bolReConnect:
                    sock.close
                    bolEnd = True
                else:
                    # Check if new command arrived from server
                    if gintLastCommand < gintTotalCommand:
                        gintLastCommand += 1

                        received = glstCommand[gintLastCommand-1]

                        if received == ":Disconnect":
                            bolEnd = True
                        
                        elif received == ":LoginOK":
                            
                            # Beep a sound when the connection is established
                            sound.beep()
                            lcd.clear()
                            lcd.draw.text((10,5),  'Server Connected')
                            lcd.update()

                        else:
                            pass
                sleep(0.1)

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
    '''The function receives signals from the server'''
    global sock, gintTotalCommand, glstCommand, bolReConnect, Release

    bolEnd = False

    while not bolEnd:
        # Receive Data From Server and store it inside the list glstCommand
        received = str(sock.recv(1024).decode())

        if received == "":
            # Socket disconnected, may be due to Wifi connection lost
            # The following codes deal with situation 1
            bolEnd = True
            bolReConnect = True

        elif received == ":LoginOK":
            
            # Beep a sound when the connection is established
            sound.beep()
            lcd.clear()
            lcd.draw.text((10,5),  'Server Connected')
            lcd.update()
        
        elif received == ":Release":
            Release = True
        
        elif received == ":Exit":
            sound.speak('Exit Exit')
            bolend = True
            sys.exit()
            
        else:
            # Normal Receive
            gintTotalCommand += 1
            glstCommand.append(received)

            if received == ":Disconnect":
                bolEnd = True

def MMT():
    global MM1
    MM1.on_for_seconds(-20,15,brake=False)

# Function to move the lift of the stocker & position of the trailer simultaneously

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
    MMTY = MoveTank(OUTPUT_B, OUTPUT_C, motor_class= MediumMotor)
    MM1 = MediumMotor(OUTPUT_A)
    MMC = MediumMotor(OUTPUT_D)
    CS1 = ColorSensor(INPUT_1)
    CS2 = ColorSensor(INPUT_2)
    CS4 = ColorSensor(INPUT_4)
    CS1.MODE_COL_REFLECT
    CS2.MODE_COL_REFLECT
    CS4.MODE_COL_REFLECT

    # Start Main Program
    funTestSocket()
except:
    # If there is any error, it will be stored in the log file in the same directory
    pass

# End Of Pard F - This is the end of the program ****************************************************************************


