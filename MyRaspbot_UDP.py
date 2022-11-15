# Created by Youssef Elashry to allow two-way communication between Python3 and Unity to send and receive strings

# Feel free to use this in your individual or commercial projects BUT make sure to reference me as: Two-way communication between Python 3 and Unity (C#) - Y. T. Elashry
# It would be appreciated if you send me how you have used this in your projects (e.g. Machine Learning) at youssef.elashry@gmail.com

# Use at your own risk
# Use under the Apache License 2.0

# Example of a Python UDP server
import time
import UdpComms as U

# Create UDP socket to use for sending (and receiving)
sock = U.UdpComms(sendIP="192.168.0.22", localIP="192.168.0.83", portTX=9995, portRX=9996, enableRX=True, suppressWarnings=True)

servoX = 90
servoY = 90

while True:
    #tx_sock.SendData('Hello')
    data = sock.ReadReceivedData()
    
    try:
        if data == "stop":
            U.car.Car_Stop()
        elif data == "w":
#             U.car.Car_Run(150, 150)
            U.car.Car_Back(150, 150)
#             time.sleep(0.5)
#             U.car.Car_Stop()
        elif data == "a":
#             U.car.Car_Left(150, 0)
#             U.car.Car_Right(0, 150)
            U.car.Car_Back(40, 150)
#             time.sleep(0.3)
#             U.car.Car_Stop()
        elif data == "s":
#             U.car.Car_Back(150, 150)
            U.car.Car_Run(150, 150)
#             time.sleep(0.5)
#             U.car.Car_Stop()
        elif data == "d":                
#             U.car.Car_Right(0, 150)
#             U.car.Car_Left(150, 0)
            U.car.Car_Back(150, 40)
#             time.sleep(0.3)
#             U.car.Car_Stop()
        elif data == "sl":                
#             U.car.Car_Spin_Left(150, 150)
            U.car.Car_Spin_Right(150, 150)
#             time.sleep(0.3)
#             U.car.Car_Stop()
        elif data == "sr":                
#             U.car.Car_Spin_Right(150, 150)
              U.car.Car_Spin_Left(150, 150)
#             time.sleep(0.3)
#             U.car.Car_Stop()
        elif data == "cam_reset":
            U.car.Ctrl_Servo(1, 90) # 90 + N
            U.car.Ctrl_Servo(2, 90) # 90 - N
            servoX = 90
            servoY = 90
            time.sleep(0.5)            
        elif data == "cu":
            if servoY <= 0:
                servoY = 0
                print("0 under")      
            else:
                servoY -= 5
                print("servoY : {0}".format(servoY))
                            
            U.car.Ctrl_Servo(2, servoY) # 90 - N
#             time.sleep(0.3)
        elif data == "cl":
            if servoX >= 180:
                print("180 over")
                servoX = 180
            else:
                servoX += 5
                print("servoX : {0}".format(servoX))                
            U.car.Ctrl_Servo(1, servoX) # 90 + N            
#             time.sleep(0.3)
        elif data == "cr":
            if servoX <= 0:
                servoX = 0
                print("0 under")      
            else:
                servoX -= 5
                print("servoX : {0}".format(servoX))
                
            U.car.Ctrl_Servo(1, servoX) # 90 - N
#             time.sleep(0.3)
        elif data == "cd":
            if servoY >= 180:
                servoY = 180
                print("180 over")
            else:
                servoY += 5
                print("servoY : {0}".format(servoY))
                            
            U.car.Ctrl_Servo(2, servoY) # 90 - N
#             time.sleep(0.3)
        elif data == "auto":
            pass
        
    except KeyboardInterrupt:
        break
#     except ConnectionResetError as e:            
#         print('ConnectionResetError')
#         break

    time.sleep(0.3)
       