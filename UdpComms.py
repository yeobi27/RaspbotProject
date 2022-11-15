# Created by Youssef Elashry to allow two-way communication between Python3 and Unity to send and receive strings

# Feel free to use this in your individual or commercial projects BUT make sure to reference me as: Two-way communication between Python 3 and Unity (C#) - Y. T. Elashry
# It would be appreciated if you send me how you have used this in your projects (e.g. Machine Learning) at youssef.elashry@gmail.com

# Use at your own risk
# Use under the Apache License 2.0
import RPi.GPIO as GPIO
import enum
import cv2
import numpy
import base64
from queue import Queue
import YB_Pcb_Car
import PID
import threading
import inspect
import ctypes
import time
import json
import requests

serverURL = 'http://192.168.0.141:8080/home'

xservo_pid = PID.PositionalPID(1.1, 0.2, 0.8)
yservo_pid = PID.PositionalPID(0.8, 0.2, 0.8)

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
face_cascadePath = "haarcascades/haarcascade_frontalface_default.xml"
# eye_cascadePath = "haarcascades/haarcascade_eye.xml" # 눈찾기 haar 파일
face_haar = cv2.CascadeClassifier(face_cascadePath)
# eye_haar = cv2.CascadeClassifier(eye_cascadePath)
font = cv2.FONT_HERSHEY_SIMPLEX

global face_x, face_y, face_w, face_h
face_x = face_y = face_w = face_h = 0
global target_valuex
target_valuex = 2048
global target_valuey
target_valuey = 2048

names = ['None', 'KSY', 'ljy', 'chs', 'ksw']

car = YB_Pcb_Car.YB_Pcb_Car()
car.Ctrl_Servo(1,90)
car.Ctrl_Servo(2,90)

#Set the GPIO port to BIARD encoding mode
GPIO.setmode(GPIO.BOARD)

#Ignore the warning message
GPIO.setwarnings(False)

AvoidSensorLeft = 21     #Left infrared obstacle avoidance sensor pin
AvoidSensorRight = 19    #Right infrared obstacle avoidance sensor pin
Avoid_ON = 22   #Infrared obstacle avoidance sensor switch pin

#Define the pins of the ultrasonic module
EchoPin = 18
TrigPin = 16

Tracking_Right1 = 11   #X1A
Tracking_Right2 = 7  #X2A
Tracking_Left1 = 13   #X1B
Tracking_Left2 = 15   #X2B

#Set pin mode
GPIO.setup(AvoidSensorLeft,GPIO.IN)
GPIO.setup(AvoidSensorRight,GPIO.IN)
GPIO.setup(Avoid_ON,GPIO.OUT)
GPIO.setup(EchoPin,GPIO.IN)
GPIO.setup(TrigPin,GPIO.OUT)
GPIO.output(Avoid_ON,GPIO.HIGH)

GPIO.setup(Tracking_Left1,GPIO.IN)
GPIO.setup(Tracking_Left2,GPIO.IN)
GPIO.setup(Tracking_Right1,GPIO.IN)
GPIO.setup(Tracking_Right2,GPIO.IN)

class UdpComms():
    isReady = False
    
    def __init__(self,sendIP,localIP,portTX,portRX,enableRX=False,suppressWarnings=True):
        """
        Constructor
        :param udpIP: Must be string e.g. "127.0.0.1"
        :param portTX: integer number e.g. 8000. Port to transmit from i.e From Python to other application
        :param portRX: integer number e.g. 8001. Port to receive on i.e. From other application to Python
        :param enableRX: When False you may only send from Python and not receive. If set to True a thread is created to enable receiving of data
        :param suppressWarnings: Stop printing warnings if not connected to other application
        """

        import socket

        self.sendIP = sendIP
        self.localIP = localIP
        self.udpSendPort = portTX
        self.udpRcvPort = portRX
        self.enableRX = enableRX
        self.suppressWarnings = suppressWarnings # when true warnings are suppressed
        self.isDataReceived = False
        self.dataRX = None

        # Connect via UDP
        self.udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet protocol, udp (DGRAM) socket
        self.udpSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # allows the address/port to be reused immediately instead of it being stuck in the TIME_WAIT state waiting for late packets to arrive.
        self.udpSock.bind((localIP, portRX)) # bind localIP

        print('Webcam Ready')
        
        # Create Receiving thread if required
        if enableRX:
#             import threading
#             print('Tread Ready')
            self.autoDriveThread = threading.Thread(target=self.AutoDriveThreadFunc, daemon=True)
            self.laneTrackingThread = threading.Thread(target=self.laneTrackingThreadFunc, daemon=True)
            self.txThread = threading.Thread(target=self.WriteUdpThreadFunc, daemon=True)
#             self.txThread.start()
            self.rxThread = threading.Thread(target=self.ReadUdpThreadFunc, daemon=True)
            self.rxThread.start()
            
                    
    def __del__(self):
        self.CloseSocket()

    def CloseSocket(self):
        # Function to close socket
        self.udpSock.close()

    def WriteUdpThreadFunc(self):
        print('WriteUdpThread Start')
          
          ####################### from here
        global isReady
        isRead = False
        fps,st,frames_to_count,cnt = (0,0,30,0)
        
        print('WriteUdpThread Start')
        
        capture = cv2.VideoCapture(0)
        capture.set(3,320)
        capture.set(4,240)
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
        capture.set(cv2.CAP_PROP_BRIGHTNESS, 62)
        capture.set(cv2.CAP_PROP_CONTRAST, 63)
        capture.set(cv2.CAP_PROP_EXPOSURE, 4800)
        
        while True:
            if self.isReady:
                
                ret, frame = capture.read()

                gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_haar.detectMultiScale(gray_img, 1.2, 4)
                    
                if ret == False:
                    continue
                
                if len(faces) > 0:

                    (face_x, face_y, face_w, face_h) = faces[0]
                    # cv2.rectangle(frame,(face_x+10,face_y),(face_x+face_w-10,face_y+face_h+20),(0,255,0),2)
                    cv2.rectangle(frame,(face_x,face_y),(face_x+face_w,face_y+face_h),(255,0,0),2)

                    # face recognition Start
                    id, confidence = recognizer.predict(gray_img[face_y:face_y+face_h,face_x:face_x+face_w])
                    # Check if confidence is less them 100 ==> "0" is perfect match
                    if (confidence < 100):
                        id = names[id]
                        # print(confidence)
                        # confidence = "  {0}%".format(round(100 - confidence))
                        confidence = "  {0}%".format(round(confidence))
                    else:
                        id = "unknown"
                        confidence = "  {0}%".format(round(confidence))
                    
                    cv2.putText(frame, str(id), (face_x+5,face_y-5), font, 1, (255,255,255), 2)
                    cv2.putText(frame, str(confidence), (face_x+5,face_y+face_h-5), font, 1, (255,255,0), 1)
                    # face recognition End

                    #Proportion-Integration-Differentiation
                    
                    if id != "unknown":
                        xservo_pid.SystemOutput = face_x + face_w/2
    #                         print("SystemOutput 1: {0}".format(xservo_pid.SystemOutput))
                        xservo_pid.SetStepSignal(150)
                        xservo_pid.SetInertiaTime(0.01, 0.1)
    #                         print("SystemOutput 2: {0}".format(xservo_pid.SystemOutput))
                        target_valuex = int(1500 + xservo_pid.SystemOutput)
    #                         print("target valuex: {0}".format(target_valuex))
                        target_servox = int((target_valuex-500)/10)
    #                         print("target servox: {0}".format(target_servox))
                        
                        if target_servox > 180:
                            target_servox = 180
                        if target_servox < 0:
                            target_servox = 0

    #                         print("face*0.5: {0}".format(face_y + face_h/2))
                        yservo_pid.SystemOutput = face_y + face_h/2
                        yservo_pid.SetStepSignal(120)
                        yservo_pid.SetInertiaTime(0.01, 0.1)
                        target_valuey = int(1500 - yservo_pid.SystemOutput)
    #                         print("target valuey: ".format(target_valuey))
                        target_servoy = int((target_valuey-500)/10)
    #                         print("target_servoy: ".format(target_servoy))
                        
                        if target_servoy > 180:
                            target_servoy = 180
                        if target_servoy < 0:
                            target_servoy = 0

                        #robot.Servo_control(target_valuex,target_valuey)
                            
                        car.Ctrl_Servo(1, target_servox)
                        car.Ctrl_Servo(2, target_servoy)

                    elif id == "unknown":
                        #pass
                        encoded,buffer = cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,80])                        
                        # send to decoded unknown info 
                        im_b64 = base64.b64encode(buffer).decode('utf8')
                        headers = {'method': 'get', 'Content-type': 'application/json', 'Accept-Charset': 'utf-8'}
                        payload = json.dumps({"image": im_b64})
                        print(payload)
                        
                        response = requests.post(serverURL, data=payload, headers=headers)
                        
                        try:
                            print(response.status_code)
                            #print(response.text)
                            #resdata = response.json()
                        except requests.exceptions.RequestException as e:
                            print(response.text)
                            print(f"RequestException occurred:\n{e}")
                            pass


                encoded,buffer = cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,80])

                message = base64.b64encode(buffer)
                self.udpSock.sendto(message,(self.sendIP, self.udpSendPort))
                
#                 frame = cv2.putText(frame,'FPS: '+str(fps),(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
                cv2.imshow('TRANSMITTING VIDEO',frame)
                
                key = cv2.waitKey(1) & 0xFF
                  
                  ##################### to Uncomment by 2022-11-08
                
#                 if key == ord('q'):
#                     self.udpSock.close()
#                     break
#                 if cnt == frames_to_count:
#                     try:
#                         print(fps)
#                         fps = round(frames_to_count/(time.time()-st))
#                         st=time.time()
#                         cnt=0
#                     except:
#                         print('fps error')
#                         pass
#                 cnt+=1

#             self.SendData()  # Send to Client Video Capture
         
    def SendData(self):
        
        # Use this function to send string to C#
        #self.udpSock.sendto(bytes(strToSend,'utf-8'), (self.sendIP, self.udpSendPort))
        self.udpSock.sendto(b'Hello', ('192.168.0.22', self.udpSendPort))
        #self.udpSock.sendto(bytes(strToSend,'utf-8'), ('192.168.0.22', 3390))

    def ReceiveData(self):
        """
        Should not be called by user
        Function BLOCKS until data is returned from C#. It then attempts to convert it to string and returns on successful conversion.
        An warning/error is raised if:
            - Warning: Not connected to C# application yet. Warning can be suppressed by setting suppressWarning=True in constructor
            - Error: If data receiving procedure or conversion to string goes wrong
            - Error: If user attempts to use this without enabling RX
        :return: returns None on failure or the received string on success
        """
        
        if not self.enableRX: # if RX is not enabled, raise error
            raise ValueError("Attempting to receive data without enabling this setting. Ensure this is enabled from the constructor")

        data = None
        try:
            #data, _ = self.udpSock.recvfrom(1024)
            data, _ = self.udpSock.recvfrom(65536)
            data = data.decode('utf-8')
            
        except WindowsError as e:
            if e.winerror == 10054: # An error occurs if you try to receive before connecting to other application
                if not self.suppressWarnings:
                    print("Are You connected to the other application? Connect to it!")
                else:
                    pass
            else:
                raise ValueError("Unexpected Error. Are you sure that the received data can be converted to a string")

        return data

    def ReadUdpThreadFunc(self): # Should be called from thread
        """
        This function should be called from a thread [Done automatically via constructor]
                (import threading -> e.g. udpReceiveThread = threading.Thread(target=self.ReadUdpNonBlocking, daemon=True))
        This function keeps looping through the BLOCKING ReceiveData function and sets self.dataRX when data is received and sets received flag
        This function runs in the background and updates class variables to read data later

        """
#         global isReady
        
        print('ReadyUdpThread Start')
        
        self.isDataReceived = False # Initially nothing received

        while True:
            print('ReadDataThreadFunc')
            data = self.ReceiveData()  # Blocks (in thread) until data is returned (OR MAYBE UNTIL SOME TIMEOUT AS WELL)
            self.dataRX = data # Populate AFTER new data is received
            self.isDataReceived = True
            
            if data == "cam_play":
                print(data)
                self.txThread.start()
                self.isReady = True
            
            if data == "cam_stop":
                print(data)
                if self.txThread.is_alive():                        
                    self.stop_thread(self.txThread)
                    self.txThread = threading.Thread(target=self.WriteUdpThreadFunc, daemon=True)                
                self.isReady = False
                
            if data == "auto_drive":
                print(data)
                self.autoDriveThread.start()                
                self.isReady = True
                
            if data == "auto_stop":
                print(data)                
                if self.autoDriveThread.is_alive():
                    self.stop_thread(self.autoDriveThread)
                    self.autoDriveThread = threading.Thread(target=self.AutoDriveThreadFunc, daemon=True)                        
                    car.Car_Stop()                                    
                self.isReady = False

            if data == "tracking_start":
                print(data)
                self.laneTrackingThread.start()                
                self.isReady = True

            if data == "tracking_stop":
                print(data)
                if self.laneTrackingThread.is_alive():
                    self.stop_thread(self.laneTrackingThread)
                    self.laneTrackingThread = threading.Thread(target=self.laneTrackingThreadFunc, daemon=True)                        
                    car.Car_Stop()
                self.isReady = False

            if data == "Bye":
                print(data)
                try:
                    if self.txThread.is_alive():                        
                        self.stop_thread(self.txThread)
                        self.txThread = threading.Thread(target=self.WriteUdpThreadFunc, daemon=True)
                    
                    if self.autoDriveThread.is_alive():
                        self.stop_thread(self.autoDriveThread)
                        self.autoDriveThread = threading.Thread(target=self.AutoDriveThreadFunc, daemon=True)
                        car.Car_Stop()
                        
                    if self.laneTrackingThread.is_alive():
                        self.stop_thread(self.laneTrackingThread)
                        self.laneTrackingThread = threading.Thread(target=self.laneTrackingThreadFunc, daemon=True)
                        car.Car_Stop()
                        
                    self.isReady = False
                    
                    print("Is txThread alive:", self.txThread.is_alive())
                    print("Is autoDriveThread alive:", self.autoDriveThread.is_alive())
                    print("Is laneTrackingThread alive:", self.laneTrackingThread.is_alive())
                    
                except Exception as e:                    
                    print(f"nothing running thread: \n{e}")
            
            # When it reaches here, data received is available

    def ReadReceivedData(self):
        """
        This is the function that should be used to read received data
        Checks if data has been received SINCE LAST CALL, if so it returns the received string and sets flag to False (to avoid re-reading received data)
        data is None if nothing has been received
        :return:
        """

        data = None

        if self.isDataReceived: # if data has been received
            self.isDataReceived = False
            data = self.dataRX
            self.dataRX = None # Empty receive buffer

        return data
    
    def laneTrackingThreadFunc(self):
        print("laneTrackingThreadFunc")
        
        while True:
            if self.isReady:
                self.tracking_function()
            
        car.Car_Stop()
        
    def AutoDriveThreadFunc(self):
        print("AutoDriveThreadFunc")
        
        while True:
            if self.isReady:
                self.avoid()
            
        car.Car_Stop()
    
    def _async_raise(self, tid, exctype):
        """raises the exception, performs cleanup if needed"""
#         print("tid: {0}".format(tid))
        tid = ctypes.c_long(tid)
#         print("tid: {0}".format(tid))
        if not inspect.isclass(exctype):
            exctype = type(exctype)
            
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            
    def stop_thread(self, thread):
        self._async_raise(thread.ident, SystemExit)
        
    #Ultrasonic function
    def Distance(self):
        GPIO.output(TrigPin,GPIO.LOW)
        time.sleep(0.000002)
        GPIO.output(TrigPin,GPIO.HIGH)
        time.sleep(0.000015)
        GPIO.output(TrigPin,GPIO.LOW)

        t3 = time.time()    # 현재시각

        while not GPIO.input(EchoPin):
            t4 = time.time()    # 현재시각 계속 갱신
            if (t4 - t3) > 0.03 :
                return -1
            
        t1 = time.time()
        
        while GPIO.input(EchoPin):
            t5 = time.time()
            if(t5 - t1) > 0.03 :
                return -1

        t2 = time.time()
        time.sleep(0.01)
        #print ("distance_1 is %d " % (((t2 - t1)* 340 / 2) * 100))
        return ((t2 - t1)* 340 / 2) * 100

    def CallDistance(self):
        num = 0
        ultrasonic = []
        while num < 5:
                distance = self.Distance()
                #print("distance is %f"%(distance) )
                while int(distance) == -1 :
                    distance = self.Distance()
                    #print("Tdistance is %f"%(distance) )
                while (int(distance) >= 500 or int(distance) == 0) :
                    distance = self.Distance()
                    #print("Edistance is %f"%(distance) )
                ultrasonic.append(distance)
                num = num + 1
    #             time.sleep(0.01)
        distance = (ultrasonic[1] + ultrasonic[2] + ultrasonic[3])/3
    #     print("distance is %f"%(distance) )
        return distance

    def avoid(self):
        distance = self.CallDistance()
        LeftSensorValue  = GPIO.input(AvoidSensorLeft)
        RightSensorValue = GPIO.input(AvoidSensorRight)
        #With obstacle pin is low level, the indicator light is on, without obstacle, pin is high level, the indicator light is off
        if distance < 15 and LeftSensorValue == False and RightSensorValue == False :
            car.Car_Stop() 
            time.sleep(0.1)
            car.Car_Spin_Right(100,100)
            time.sleep(1)
        elif distance < 15 and LeftSensorValue == True and RightSensorValue == False :
            car.Car_Stop()
            time.sleep(0.1)
            car.Car_Spin_Left(80,80)
            time.sleep(1)
            if LeftSensorValue == False and RightSensorValue == True :
                car.Car_Stop()
                time.sleep(0.1)
                car.Car_Spin_Right(90,90) 
                time.sleep(2)
        elif distance < 15 and LeftSensorValue == False and RightSensorValue == True :
            car.Car_Stop()
            time.sleep(0.1)
            car.Car_Spin_Right(80,80)
            time.sleep(1)
            if LeftSensorValue == True and RightSensorValue == False  :
                car.Car_Stop()
                time.sleep(0.1)
                car.Car_Spin_Left(90,90) 
                time.sleep(2)
        elif distance < 15 and LeftSensorValue == True and RightSensorValue == True :
            car.Car_Stop()
            time.sleep(0.1)
            car.Car_Spin_Right(80,80) 
            time.sleep(0.5)
        elif distance >= 15 and LeftSensorValue == False and RightSensorValue == False :
            car.Car_Stop()
            time.sleep(0.1)
            car.Car_Spin_Right(90,90)
            time.sleep(1)
        elif distance >= 15 and LeftSensorValue == False and RightSensorValue == True :
            car.Car_Stop()
            time.sleep(0.1)
            car.Car_Spin_Right(80,80)
            time.sleep(0.5)
        elif distance >= 15 and LeftSensorValue == True and RightSensorValue == False :
            car.Car_Stop()
            time.sleep(0.1)
            car.Car_Spin_Left(80,80)
            time.sleep(0.5)
        else:
#             car.Car_Run(100,100)
            car.Car_Back(90,90)
        
    def tracking_function(self):
        Tracking_Left1Value = GPIO.input(Tracking_Left1);
        Tracking_Left2Value = GPIO.input(Tracking_Left2);
        Tracking_Right1Value = GPIO.input(Tracking_Right1);
        Tracking_Right2Value = GPIO.input(Tracking_Right2);
        
            # 0 0 X 0
            # 1 0 X 0
            # 0 1 X 0
        if (Tracking_Left1Value == False or Tracking_Left2Value == False) and  Tracking_Right2Value == False:
            car.Car_Spin_Right(70, 30)
            time.sleep(0.2)
     
            # 0 X 0 0       
            # 0 X 0 1 
            # 0 X 1 0       
        elif Tracking_Left1Value == False and (Tracking_Right1Value == False or  Tracking_Right2Value == False):
            car.Car_Spin_Left(30, 70) 
            time.sleep(0.2)
      
            # 0 X X X
        elif Tracking_Left1Value == False:
            car.Car_Spin_Left(70, 70) 
            time.sleep(0.05)
            # X X X 0
        elif Tracking_Right2Value == False:
            car.Car_Spin_Right(70, 70)
            time.sleep(0.05)
            # X 0 1 X
        elif Tracking_Left2Value == False and Tracking_Right1Value == True:
            car.Car_Spin_Left(60, 60) 
            time.sleep(0.02)
            # X 1 0 X  
        elif Tracking_Left2Value == True and Tracking_Right1Value == False:
            car.Car_Spin_Right(60, 60)
            time.sleep(0.02)
       
            # X 0 0 X
        elif Tracking_Left2Value == False and Tracking_Right1Value == False:
            car.Car_Run(70, 70)
