#!/usr/bin/env python3
from ev3dev2.display import Display
from ev3dev2.button import Button
from ev3dev2.sound import Sound
from ev3dev2.motor import LargeMotor, MediumMotor
from ev3dev2.motor import MoveTank
from ev3dev2.motor import OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.sensor.lego import ColorSensor
from ev3dev2.sensor import INPUT_1, INPUT_2
from time import sleep, time
from multiprocessing import Process
import datetime, traceback, math, json, socket, threading, sys, random

# for debuging
def debug_print(*args, **kwargs):
    '''Print debug messages to stderr.

    This shows up in the output panel in VS Code.
    '''
    print(*args, **kwargs, file=sys.stderr)

def reset_console():
    '''Resets the console to the default state'''
    print('\x1Bc', end='')

def set_cursor(state):
    '''Turn the cursor on or off'''
    if state:
        print('\x1B[?25h', end='')
    else:
        print('\x1B[?25l', end='')

def set_font(name):
    '''Sets the console font

    A full list of fonts can be found with `ls /usr/share/consolefonts`
    '''
    os.system('setfont ' + name)


def debuging_print(x):
    '''The main function of our program'''

    # set the console just how we want it
    reset_console()
    set_cursor(OFF)
    set_font('Lat15-Terminus24x12')

    # print something to the screen of the device
    print(x)

    # print something to the output panel in VS Code
    debug_print(x)

    # wait a bit so you have time to look at the display before the program
    # exits

def StartServerSocket():
    ''' The function create the socket and send command to each crane & input device'''

    # Variables for socket connection
    global sock1, sock2, sock3, connection1, connection2, connection3
    # Counting the received message from Crane1
    global gintTotalCommand1, gintLastCommand1, glstCommand1, gbolConnect1
    # Counting the received message from Crane2
    global gintTotalCommand2, gintLastCommand2, glstCommand2, gbolConnect2
    # Counting the received message from Input1
    global gintTotalCommand3, gintLastCommand3, glstCommand3, gbolConnect3
    # Identifier of the state of each section (whether they are able to receive command or not)
    global Null1, Null2, Null3
    # Command Code List
    global CmdList

    # Chr for message 
    # it will be converted in the client using ascii code system e.g. A = 65 / B = 66
    # X Coordinate
    xc = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V")
    # 3 Floors (Y coordinate)
    yc = ("A", "B", "C")
    # Shelf identifier chr (left or right)
    LR = ("A", "B")
    # In / out identifier chr (Take in or out the Cartridge)
    IO = ("A", "B")
    # Chr for command (Command Identifier)
    count = ("M")

    # Set the initial Position of Crane1 and Crane2
    C1Xc = "A"
    C2Xc = "V"

    # Initialize Null Values. It prevents the unexpected movement of crane and input device at the beginning
    Null1 = False
    Null2 = False
    Null3 = False

    # Command List the server has to send to the Cranes and Input section
    CmdList = []

    # Generate a random task list and run (This is a demo. The code can be changed)
    # The rule for a code:
    # 1st chr: Crane Identifier (Crane 1 or 2)
    # 2nd chr: In / Out Identifier (A: out B: In)
    # 3rd chr: Shelf Identifier (A: Left B: Right (seeing from x=0)
    # 4th chr: X coordinate Identifier (From A to V (A=0, B=1, ...) (A, V: Origin Point / B, T: In/out point)
    # 5th chr: Y coordinate (Floor of shelf) Identifier (From A to C)
    # 6th chr: Time identifier (Be able to set the time between the command)
    # Example: ABAHCA - Crane 1 puts a cartridge in the 3rd floor, 6th left shelf
    for i in range (1000):
        
        
        CmdList.append("AAABAA")
        CmdList.append("ABAMCA")
        CmdList.append("BAAMCA")
        CmdList.append("BBBTAA") 
        CmdList.append("AAABAA")
        CmdList.append("ABALBA")
        CmdList.append("AAABAA") 
        CmdList.append("ABBLCA")
        CmdList.append("BABLCA")
        CmdList.append("BBBSAA")
        CmdList.append("BAALBA")
        CmdList.append("BBAOBA")
        CmdList.append("BAAOBA")
        CmdList.append("BBBLCA")
        CmdList.append("AAABAA")
        CmdList.append("ABALAA")
        CmdList.append("AABLCA")
        CmdList.append("ABAFBA")
        CmdList.append("BAALAA")
        CmdList.append("BBBSBA")
        CmdList.append("AAABAA")
        CmdList.append("ABBLAA")
        CmdList.append("BABTAA")
        CmdList.append("BBBIBA")
        CmdList.append("AAAFBA")
        CmdList.append("ABBLBA")
        CmdList.append("BABLAA")
        CmdList.append("BBBNCA")
        CmdList.append("AAABAA")
        CmdList.append("ABBIAA")
        CmdList.append("BABSBA")
        CmdList.append("BBALAA")
        CmdList.append("AAALAA")
        CmdList.append("ABBDAA")
        CmdList.append("BABIAA")
        CmdList.append("BBBOCA")
        CmdList.append("AABDAA")
        CmdList.append("ABALAA")
        CmdList.append("BABNCA")
        CmdList.append("BBBLAA")
        CmdList.append("AABIBA")
        CmdList.append("ABBDAA")
        CmdList.append("BABOCA")
        CmdList.append("BBBIAA")
        CmdList.append("AABDAA")
        CmdList.append("ABALCA")
        CmdList.append("BABLBA")
        CmdList.append("BBBRBA")
        CmdList.append("AABIAA")
        CmdList.append("ABADBA")
        CmdList.append("BABRBA")
        CmdList.append("BBBMBA")
        CmdList.append("BAALCA") 
        CmdList.append("BBAUAA")
        CmdList.append("AABLAA")
        CmdList.append("ABAGBA")
        CmdList.append("BABSAA")
        CmdList.append("BBBLBA")
        CmdList.append("BABMBA")
        CmdList.append("BBAUAA")
        CmdList.append("BABLBA")
        CmdList.append("BBAUAA")
        CmdList.append("AAAGBA")
        CmdList.append("ABBLAA")
        CmdList.append("BAALAA")
        CmdList.append("BBAUAA") 
        CmdList.append("AAADBA")
        CmdList.append("ABBKAA")
        CmdList.append("BABLAA")
        CmdList.append("BBAUAA")
        CmdList.append("BABKAA")
        CmdList.append("BBAUAA")
        
    # Main Connection
    # sock.bind(('', PORT1, PORT2, PORT3))
    # Sock1: Crane 1 / Sock2: Crane 2 / Sock3: Input
    # Server does not need the clients' ip addresses
    # Server should select the port to use
    # When the port does not work, please change the port number
    # If wifi is used, please do port forwarding in advance of running the code
    # Select the port number among the opened port number
    sock1.bind(('', 8513))
    sock2.bind(('', 8507))
    sock3.bind(('', 8515))

    # Allow one client connection for each socket
    sock1.listen(1)
    sock2.listen(1)
    sock3.listen(1)

    # Beep when the socket is ready. When master beeps, pleaes turn on the client programs
    sound = Sound()
    sound.beep()
    sound.beep()
    sound.beep()

    while True:
        # Accept from the Clients
        gbolConnect1 = True
        gbolConnect2 = True
        gbolConnect3 = True

        # Init Variables which are used to receive commands in the main thread
        gintTotalCommand1 = 0
        gintLastCommand1 = 0
        glstCommand1 = []
        gintTotalCommand2 = 0
        gintLastCommand2 = 0
        glstCommand2 = []
        gintTotalCommand3 = 0
        gintLastCommand3 = 0
        glstCommand3 = []

        # To avoid the Socket Server stops at sock.recv (here we use blocking mode),
        # Here we start the sock.recv in another thread *VERY IMPORTANT*
        Process_receive1 = threading.Thread(target = StartServerReceive1)
        Process_receive1.daemon = True
        Process_receive1.start()
        
        Process_receive2 = threading.Thread(target = StartServerReceive2)
        Process_receive2.daemon = True
        Process_receive2.start()
        
        Process_receive3 = threading.Thread(target = StartServerReceive3)
        Process_receive3.daemon = True
        Process_receive3.start()
        
        EmergencyThread = threading.Thread(target = EmergencyStop)
        EmergencyThread.daemon = True
        EmergencyThread.start()

        # Run the while loop to send the commands in order
        # This loop does not stop unless the connection is lost from any client or Emergency code is sent from the server
        while gbolConnect1 and gbolConnect2 and gbolConnect3:
            
            for Cmd in CmdList:
                onetwo = Cmd[0][:]
                inout = Cmd[1][:]
                leftright = Cmd[2][:]
                Xc = Cmd[3][:]
                Yc = Cmd[4][:]
                stbtime = Cmd[5][:]

                OneDestination = inout+leftright+Xc+Yc
                debug_print(Cmd)
                # Emergency Stop Case
                if onetwo == "Z":
                    while True:
                        if Null1 and Null2:
                            # Send stop code to each client
                            connection1.sendall("ZZZ".encode())
                            connection2.sendall("ZZZ".encode())
                            connection3.sendall(":Exit".encode())
                            break
                        else:
                            sleep(0.01)
                    # Exit the Loop by making boolean values false
                    gbolConnect1 = False
                    gbolConnect2 = False
                    gbolConnect3 = False
                    sleep(0.5)
                    sys.exit()

                # Crane 1 Task
                elif onetwo == "A":
                    # Number of shelf to go
                    xcor1 = Xc[:]
                    OneOp = True
                    while OneOp:
                        # Check whether Crane 1 can receive a command
                        if Null1:
                            # When the Crane 2 has move out from the position Crane 1 will go 
                            if ord(C2Xc) - ord(xcor1) < 4:
                                MO = count+xcor1
                                Moveout = True
                                while Moveout:
                                    if Null2:
                                        connection2.sendall(MO.encode())
                                        Null2 = False
                                        # When the Crane 2 has to move to the origin point
                                        if ord(xcor1) <= 85 and ord(xcor1) > 81:
                                            sleep(2.5)
                                            C2Xc = chr(86)
                                        else:
                                            C2Xc = chr(ord(xcor1)+4)
                                        sleep(0.3)
                                        # when the crane should get the cartridge from the input point
                                        if xcor1 == "B":
                                            wait = True
                                            while wait:
                                                # Check the state of the input point (Whether the cartridege is loaded)
                                                if Null3 == True:
                                                    connection1.sendall(OneDestination.encode())
                                                    Null3 = False
                                                    Null1 = False
                                                    wait = False
                                                    C1Xc = chr(ord(xcor1))
                                                    Moveout = False
                                                    OneOp = False
                                                else:
                                                    sleep(1)
                                        else:
                                            connection1.sendall(OneDestination.encode())
                                            Null1 = False
                                            C1Xc = chr(ord(xcor1))
                                            Moveout = False
                                            OneOp = False
                                    else:
                                        sleep(1)
                            # When the Crane2 does not have to move out from its current location 
                            else:
                                if xcor1 == "B":
                                    wait = True
                                    while wait:
                                        if Null3 == True:
                                            connection1.sendall(OneDestination.encode())
                                            Null3 = False
                                            Null1 = False
                                            wait = False
                                            C1Xc = chr(ord(xcor1))
                                            OneOp = False
                                        else:
                                            sleep(1)
                                else:
                                    connection1.sendall(OneDestination.encode())
                                    Null1 = False
                                    C1Xc = chr(ord(xcor1))
                                    OneOp = False
                        # When the crane is already doing the task
                        else:
                            # wait for 1 second and check again
                            sleep(1)
                    else:
                        pass
                
                # Crane2 Task
                else:
                    xcor2 = Xc[:]
                    TwoOp = True
                    while TwoOp:
                        if Null2:
                            if ord(xcor2) - ord(C1Xc) < 4:
                                MO = count+xcor2
                                Moveout = True
                                while Moveout:
                                    if Null1:
                                        connection1.sendall(MO.encode())
                                        Null1 = False
                                        if ord(xcor2) < 70  and ord(xcor2) >= 66:
                                            sleep(2.5)
                                            C1Xc = chr(65)
                                        else:
                                            C1Xc = chr(ord(xcor2)-4)
                                        sleep(0.3)
                                        if xcor2 == "B":
                                            wait = True
                                            while wait:
                                                if Null3 == True:
                                                    connection2.sendall(OneDestination.encode())
                                                    wait = False
                                                    Null3 = False
                                                    Null2 = False
                                                    C2Xc = chr(ord(xcor2))
                                                    Moveout = False
                                                    TwoOp = False
                                                else:
                                                    sleep(1)
                                        else:
                                            connection2.sendall(OneDestination.encode())
                                            Null2 = False
                                            C2Xc = chr(ord(xcor2))
                                            Moveout = False
                                            TwoOp = False
                                    else:
                                        sleep(1)
                            else:
                                if xcor2 == "B":
                                    wait = True
                                    while wait:
                                        if Null3 == True:
                                            connection2.sendall(OneDestination.encode())
                                            wait = False
                                            Null2 = False
                                            Null3 = False
                                            C2Xc = chr(ord(xcor2))
                                            TwoOp = False
                                        else:
                                            sleep(1)
                                else:
                                    connection2.sendall(OneDestination.encode())
                                    Null2 = False
                                    C2Xc = chr(ord(xcor2))
                                    TwoOp = False
                        else:
                            sleep(1)
                    else:
                        pass

                sleep(0.1)

# *** BUG ***

# Function to receive data from Crane1, this function is to be started in another thread
def StartServerReceive1():
    '''The function receives signals from each client'''
    global gintTotalCommand1, glstCommand1
    global connection1, gbolConnect1 , sock1
    global Null1

    debug_print('acep1')
    connection1, address1 = sock1.accept()
    connection1.settimeout(None)

    bolEnd = False
    debug_print('Receive1 Start')
    while not bolEnd:
        try:
            # Receive Data From Client and store it inside the list glstCommand
            received1 = connection1.recv(2048).decode()

            # Initial Login process 
            # Check the connection is well established by sending the code
            if received1 == ":Login":
                
                connection1.sendall(":LoginOK".encode())
                debug_print('Crane1 Login')
            # When the Crane 1 finishes its task
            elif received1 == ":Finished1":
                Null1 = True
                debug_print('Crane1 Fini')
            # When the Crane 1 is arrived at the input point
            elif received1 == ":Readyforload":
                # Command input point to elevate the cartridge
                connection3.sendall(":Release".encode())
                debug_print('Crane1 Ready')
            else:
                # Normal Receive
                gintTotalCommand1 += 1
                glstCommand1.append(received1)
                debug_print('Crane1 Else')
                # If got logout from client, end this thread
                if received1 == ":End":
                    bolEnd = True
                    debug_print('Crane1 Else')
        except socket.timeout:
            # print 'time out'
            gbolHeartBeat1 = False
            gbolHeartBeat2 = False
            bolEnd = True
            gbolConnect1 = False
            gbolConnect2 = False
            gbolConnect3 = False

# Function to receive data from Crane2, this function is to be started in another thread
def StartServerReceive2():
    global gintTotalCommand2, glstCommand2
    global connection2, gbolConnect2, sock2
    global Null2
    
    bolEnd = False

    debug_print('acep2 ')
    connection2, address1 = sock2.accept()
    connection2.settimeout(None)

    debug_print('Receive2 Start')
    while not bolEnd:
        try:
            # Receive Data From Client and store it inside the list glstCommand
            received2 = connection2.recv(2048).decode()
            
            # Initial Login process 
            # Check the connection is well established by sending the code
            if received2 == ":Login":
                debug_print('Crane2 Login')
                connection2.sendall(":LoginOK".encode())

            # When the Crane 2 finishes its task
            elif received2 == ":Finished2":
                Null2 = True
                debug_print('Crane2 Finished')
            # When the Crane 2 arrives at the input point
            elif received2 == ":Readyforload":
                # Command input point to elevate the cartridge
                connection3.sendall(":Release".encode())
                debug_print('Crane2 Ready')
            else:
                # Normal Receive
                gintTotalCommand2 += 1
                glstCommand2.append(received2)
                debug_print('Crane2 Else')
                # If got logout from client, end this thread
                if received2 == ":End":
                    bolEnd = True
        
        except socket.timeout:
            # print 'time out'
            bolEnd = True
            gbolConnect1 = False
            gbolConnect2 = False
            gbolConnect3 = False

# Function to receive data from Input, this function is to be started in another thread
def StartServerReceive3():
    global gintTotalCommand3, glstCommand3
    global connection3, gbolConnect3, sock3
    global Null3

    debug_print('acep3 ')
    connection3, address1 = sock3.accept()
    connection3.settimeout(None)
    debug_print('Receive3 Start')
    bolEnd = False

    while not bolEnd:
        try:
            # Receive Data From Client and store it inside the list glstCommand
            received3 = connection3.recv(2048).decode()

            # Initial Login process 
            # Check the connection is well established by sending the code
            if received3 == ":Login":
                # Beep a Sound
                sound.beep()
                connection3.sendall(":LoginOK".encode())
                debug_print('Input Login')
            elif received3 == ":Finished3":
                Null3 = True
                debug_print('Input Fini')
            else:
                # Normal Receive
                gintTotalCommand3 += 1
                glstCommand3.append(received3)

                # If got logout from client, end this thread
                if received3 == ":End":
                    bolEnd = True
        
        except socket.timeout:
            # print 'time out'
            bolEnd = True
            gbolConnect1 = False
            gbolConnect2 = False
            gbolConnect3 = False

# Emergency Stop Function
def EmergencyStop():
    global Null1, Null2
    global connection1, connection2, connection3
    global CmdList

    while True:
        # When any button of the master brick is pressed
        if btn.any():
            for i in range (1000):
                # Change the whole component of list to emergency stop code
                CmdList[i] = "ZZZZZZ"
            # Beep a sound
            sound.play_tone(1500, 2)
            sound.speak('Exit Exit')
        else:
            sleep(0.01)

try:
    # Start Main Program
    # Create Socket
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Sound
    sound = Sound()
    # Button
    btn = Button()
    # Main Thread
    StartServerSocket()
except:
    pass
