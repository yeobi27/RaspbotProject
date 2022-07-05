from kivy.config import Config

# 크기 조정 안함
Config.set('graphics', 'resizable', False)

from kivy.core.window import Window

Window.size = (400, 600)
# Window.size = (1440, 2560)

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


def recvall(sock, count):
    buf = b''
    try:
        step = count
        while True:
            print("count : " + str(count))
            data = sock.recv(step)
            buf += data
            print("buf len : " + str(len(buf)))
            if len(buf) == count:
                break
            elif len(buf) < count:
                step = count - len(buf)
                print("step: " + str(step))
    except Exception as e:
        print(e)
    # s[:5]	#'Hello' - index 0 ~ 4까지 출력
    # buf 안에 count 만큼 출력
    return buf[:count]


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

clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


class main(BoxLayout):
    ipAddress = None
    port = None

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
                self.ids.status.text = "Stop"
                try:
                    clientsocket.connect((self.ipAddress, self.port))
                    Clock.schedule_interval(self.recv, 0.05)
                except:
                    print("already connect!")
                    Clock.schedule_interval(self.recv, 0.05)


    def closePopup(self, btn):
        self.popup1.dismiss()

    def stop(self):
        self.ids.status.text = "Play"
        Clock.unschedule(self.recv)

    def recv(self, dt):

        message = '1'
        clientsocket.send(message.encode())

        length = recvall(clientsocket, 16)
        stringData = recvall(clientsocket, int(length))
        data = np.frombuffer(stringData, dtype='uint8')

        decimg = cv2.imdecode(data, 1)

        buffer = cv2.flip(decimg,0).tostring()

        texture = Texture.create(size=(decimg.shape[1], decimg.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
        self.ids.image_source.texture = texture


    def carRun(self):
        message = 'w'
        clientsocket.send(message.encode())

    def carBack(self):
        message = 's'
        clientsocket.send(message.encode())

    def carLeft(self):
        message = 'a'
        clientsocket.send(message.encode())

    def carRight(self):
        message = 'd'
        clientsocket.send(message.encode())

    def carSpinLeft(self):
        message = 'sl'
        clientsocket.send(message.encode())

    def carSpinRight(self):
        message = 'sr'
        clientsocket.send(message.encode())

    def camUp(self):
        message = 'cu'
        clientsocket.send(message.encode())

    def camLeft(self):
        message = 'cl'
        clientsocket.send(message.encode())

    def camRight(self):
        message = 'cr'
        clientsocket.send(message.encode())

    def camDown(self):
        message = 'cd'
        clientsocket.send(message.encode())

    def close(self):
        clientsocket.close()
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
            print(", port : ", self.port)
        except:
            pass
        self.popup.dismiss()


class videoStreamApp(App):
    def build(self):
        Window.clearcolor = (1, 1, 1, 1)
        return Builder.load_string(kv)


videoStreamApp().run()
