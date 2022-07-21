from kivy.config import Config

# 크기 조정 안함
Config.set('graphics', 'resizable', False)

from kivy.core.window import Window

Window.size = (400, 600)
# Window.size = (700, 900)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
import socket
from threading import *
from kivy.uix.image import Image
from kivy.cache import Cache
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
import numpy as np
import cv2
import base64
import time

BUFF_SIZE = 65536
host_ip = '192.168.0.83'  # socket.gethostbyname(host_name)
port_in = 9995			  # rx
port_out = 9996		 	  # tx

# create SEND socket
send_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# create Receive socket
rcv_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rcv_client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)

kv = '''
main:
    BoxLayout:
        orientation: 'vertical'
        padding: root.width * 0.05, root.height * .05
        spacing: '5dp'
        BoxLayout:
            size_hint: [1,2]
            padding: '5dp'
            spacing: '10dp'
            canvas:
                Color:
                    rgb: .3, .2, .5
                Line:
                    width: 1.2
                    rectangle: (self.x, self.y, self.width, self.height)            
            Image:
                id: image_source
                source: 'Images/Cam.jpg'
        GridLayout:
            cols: 2                
            BoxLayout:
                size_hint: [.5,1]
                GridLayout:
                    cols: 3
                    padding: '5dp'
                    spacing: '10dp'
                    canvas:
                        Color:
                            rgb: .3, .2, .5
                        Line:
                            width: 1.2
                            rectangle: (self.x, self.y, self.width, self.height)
                    Button:
                        text:'Setting'
                        bold: True
                        on_press: root.setting()
                    Button:
                        id: status
                        text:'Play'
                        bold: True
                        on_press: root.playPause()
                    Button:
                        text:'Close'
                        bold: True        
                        on_press: root.close()            
                    Button:
                        text: 'LS'
                        bold: True
                        on_press: root.carSpinLeft()
                    Button:
                        text: 'W'
                        bold: True
                        on_press: root.carRun()
                    Button:
                        text: 'RS'
                        bold: True
                        on_press: root.carSpinRight()
                    Button:
                        text: 'A'
                        bold: True
                        on_press: root.carLeft()
                    Button:
                        text: 'S'
                        bold: True
                        on_press: root.carBack()
                    Button:
                        text: 'D'
                        bold: True
                        on_press: root.carRight()
            BoxLayout:        
                size_hint: [.5,1]
                GridLayout:
                    cols: 3
                    padding: '5dp'
                    spacing: '10dp'
                    canvas:
                        Color:
                            rgb: .1, .2, .5
                        Line:
                            width: 1.2
                            rectangle: (self.x, self.y, self.width, self.height)
                    Label:
                        text: ""
                    Button:
                        text: 'cam_UP'
                        bold: True
                        on_press: root.camUp()
                    Label:
                        text: ""
                    Button:
                        text: 'cam_A'
                        bold: True
                        on_press: root.camLeft()
                    Label:
                        text: ""
                    Button:
                        text: 'cam_D'
                        bold: True
                        on_press: root.camRight()
                    Label:
                        text: ""
                    Button:
                        text: 'cam_Down'
                        bold: True
                        on_press: root.camDown()
                    Label:
                        text: ""
'''

class main(BoxLayout):
    ipAddress = None
    port = None
    rcv_client_socket.bind(('192.168.0.22', port_in)) # local host and recv port
    fps, sec, frames_to_count, cnt = (0, 0, 30, 0)

    def playPause(self):
        if self.ipAddress == None or self.port == None:
            box = GridLayout(cols=1)
            box.add_widget(Label(text="Ip or Port Not Set"))
            btn = Button(text="OK")
            btn.bind(on_press=self.closePopup)
            box.add_widget(btn)
            self.popup1 = Popup(title='Error', content=box, size_hint=(.8, .3))
            self.popup1.open()
        else:
            if self.ids.status.text == "Stop":
                self.stop()
            else:
                try:
                    # clientsocket.connect((self.ipAddress, self.port))
                    message = 'Hello'
                    send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))
                    self.ids.status.text = "Stop"
                    Clock.schedule_interval(self.recv, 0.02)
                except:
                    print("sendto error or already connect!")
                    # error popup
                    box = GridLayout(cols=1)
                    box.add_widget(Label(text="Ip or Port Not right format."))
                    btn = Button(text="OK")
                    btn.bind(on_press=self.closePopup)
                    box.add_widget(btn)
                    self.popup1 = Popup(title='Error', content=box, size_hint=(.8, .3))
                    self.popup1.open()


    def closePopup(self, btn):
        self.popup1.dismiss()

    def stop(self):
        try:
            message = 'Bye'
            send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))
            time.sleep(0.5)
            self.ids.status.text = "Play"
            Clock.unschedule(self.recv)
        except:
            print("stop error")

    def recv(self, dt):

        packet, _ = rcv_client_socket.recvfrom(BUFF_SIZE)

        data = base64.b64decode(packet, ' /')
        npdata = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(npdata, 1)

        frame = cv2.putText(frame, 'FPS: ' + str(self.fps), (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 0)

        if self.cnt == self.frames_to_count:
            try:
                print(self.frames_to_count)
                print((time.time() - self.sec))
                self.fps = round(self.frames_to_count / (time.time() - self.sec))
                self.sec = time.time()
                self.cnt = 0
            except:
                print("fps except")
                pass
        self.cnt += 1

        buffer = cv2.flip(frame, 0).tobytes()

        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
        self.ids.image_source.texture = texture

    def carRun(self):
        message = 'w'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def carBack(self):
        message = 's'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def carLeft(self):
        message = 'a'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def carRight(self):
        message = 'd'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def carSpinLeft(self):
        message = 'sl'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def carSpinRight(self):
        message = 'sr'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def camUp(self):
        message = 'cu'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def camLeft(self):
        message = 'cl'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def camRight(self):
        message = 'cr'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def camDown(self):
        message = 'cd'
        send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))

    def close(self):
        try:
            message = 'Bye'
            send_client_socket.sendto(message.encode('UTF-8'), (self.ipAddress, self.port))
            time.sleep(0.5)
            rcv_client_socket.close()
            send_client_socket.close()
            App.get_running_app().stop()
        except:
            print("close")
            App.get_running_app().stop()

    def setting(self):
        box = GridLayout(cols=2)
        box.add_widget(Label(text="IpAddress: ", bold=True))
        # self.st = TextInput(id="serverText")
        self.st = TextInput()
        box.add_widget(self.st)
        box.add_widget(Label(text="Port: ", bold=True))
        self.pt = TextInput()
        # self.pt = TextInput(id="portText")
        box.add_widget(self.pt)
        btn = Button(text="Set", bold=True)
        btn.bind(on_press=self.settingProcess)
        box.add_widget(btn)
        self.popup = Popup(title='Settings', content=box, size_hint=(.6, .4))
        self.popup.open()

    def settingProcess(self, btn):
        try:
            self.ipAddress = self.st.text
            self.port = int(self.pt.text)
            print("ip : ", self.ipAddress)
            print("port : ", self.port)
        except:
            pass
        self.popup.dismiss()


class videoStreamApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        return Builder.load_string(kv)


videoStreamApp().run()
