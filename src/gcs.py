import numpy as np
import serial
from threading import Thread
import tkinter as tk
import time
from PIL import Image, ImageTk
import cv2
from datetime import datetime
from pathlib import Path
import os

INC = 50
MAX = 1700
MIN = 1300

class GCS(tk.Tk):
    ''' Ground Control System
            Extends a Tkinter window
    '''

    def __init__(self, *args, **kwargs):

        # Init Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_title("Laser Bot GCS")
        self.img_laser = np.zeros((400,400),dtype=np.uint8)
        self.tk_img_laser = ImageTk.PhotoImage(image=Image.fromarray(self.img_laser).resize((800,800),Image.LANCZOS))
        self.label_laser = tk.Label(self, image=self.tk_img_laser)
        self.label_laser.pack(side=tk.TOP)
        self.img_camera = np.zeros((400,400),dtype=np.uint8)
        self.tk_img_camera = ImageTk.PhotoImage(image=Image.fromarray(self.img_camera))
        self.label_camera = tk.Label(self, image=self.tk_img_camera)
        self.label_camera.pack(side=tk.BOTTOM)
        # Logging, data collection
        self.logdir = f'{datetime.now():%Y%m%d_%H%M%S}'
        Path(self.logdir).mkdir(exist_ok=True)
        self.logfile = open(f'{self.logdir}/gcs_{datetime.now():%H%M%S}.log','w')

        # Handle SiK Radio
        try:
            self.sik_port = serial.Serial('/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_D30GKCRB-if00-port0',115200,timeout=None)
            self.sik_thread = Thread(target=self.read_sik, daemon=True)
            self.sik_thread.start()
        except:
            print('Could not open SiK interface')

        # Camera Tracking
        os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;udp'
        # USB camera
        #self.cap = cv2.VideoCapture(0)
        # RTSP camera
        self.cap = cv2.VideoCapture('rtsp://admin:AMCAMSL7248@192.168.168.222//Preview_01_main',cv2.CAP_FFMPEG)

        self.aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
        self.aruco_params = cv2.aruco.DetectorParameters_create()
        self.camera_thread = Thread(target=self.read_cam, daemon=True)
        if self.cap.isOpened():
            self.camera_thread.start()

        # Events
        self.bind('<KeyPress>', self.key_press)
        self.last_press = time.time()
        self.timer = self.after(50,self.update)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        

        # State
        self.thrust = 1500
        self.rudder = 1500

    
    '''
    Utility Functions
    '''
    def log_data(self, src_id, data, display=True):
        entry = f'{datetime.now():%Y%m%d,%H%M%S,%f},{src_id},{np.array2string(data, max_line_width=np.inf,separator=',',prefix='',suffix='')[1:-1]}\n'
        if display:
            print(entry,end='')
        self.logfile.write(entry)


    def set_thrust(self,increase=True):
        if increase: d=INC
        else: d=-INC
        self.thrust = max(MIN,min(MAX,self.thrust+d))
    def set_rudder(self,increase=True):
        if increase: d=INC
        else: d=-INC
        self.rudder = max(MIN,min(MAX,self.rudder+d))
    def stop(self):
        self.thrust = 1500
        self.rudder = 1500
        self.send_cmd()
    def send_cmd(self):
        cmd = f'$CMD,{self.thrust:+04d},{self.rudder:+04d}\n'
        try:
            self.sik_port.write(cmd.encode())
            print(cmd)
        except:
            print('Could not send cmd')

    def update(self):
        ''' Update
                Periodically refreshes the view image
                and monitors system state
        '''
        # Update and scale view image
        self.tk_img_laser = ImageTk.PhotoImage(
                image=Image.fromarray(self.img_laser))#.resize((800,800),Image.LANCZOS))
        self.label_laser.configure(image = self.tk_img_laser)


        # Check camera for vessel and display
        cv2.imwrite(f'{self.logdir}/{datetime.now():%Y%m%d_%H%M%S_%f}.jpg',self.img_camera)
        marker_corners, marker_ids, rejected_candidates = cv2.aruco.detectMarkers(
            self.img_camera, self.aruco_dict, parameters=self.aruco_params)
        if marker_ids is not None:
            for i, marker in enumerate(marker_ids):
                self.logfile.flush()
                self.log_data(f'ARUCO_{marker[0]}', marker_corners[i].flatten())
                self.img_camera = cv2.aruco.drawDetectedMarkers(self.img_camera, marker_corners, marker_ids)
        self.tk_img_camera = ImageTk.PhotoImage(
                image=Image.fromarray(cv2.resize(self.img_camera,
                                                 None,fx=0.3,fy=0.3,interpolation=cv2.INTER_NEAREST)))
        self.label_camera.configure(image = self.tk_img_camera)
        
        # Check watchdog timeout
        if (time.time() - self.last_press) > 6:
            self.stop()
            self.last_press = time.time()

        # re-trigger update
        self.timer = self.after(100,self.update)


    def on_closing(self):
        self.stop()
        self.cap.release()
        time.sleep(1)
        self.destroy()


    def key_press(self, event):
        ''' Keyboard callback
                generates state commands as needed
        '''
        if event.keysym == 'Up':
            self.set_thrust(True)
        elif event.keysym == 'Down':
            self.set_thrust(False)
        elif event.keysym == 'Right':
            self.set_rudder(True)
        elif event.keysym == 'Left':
            self.set_rudder(False)
        elif event.keysym == 'q':
            self.stop()
            self.cap.release()
            time.sleep(1)
            self.destroy()
        else:
            self.stop()
        self.send_cmd()
        self.last_press = time.time()
    

    def read_sik(self):
        ''' Serial input thread
                monitors received data on SiK radio
                updates view image data
        '''
        while True:
            pkt = self.sik_port.read_until(b'\xFF',1024)
            if len(pkt) == 736:
                timestamp =pkt[:15]
                #print(len(pkt))
                self.ranges = np.frombuffer(pkt[15:-1],dtype=np.uint8)
                self.log_data('LIDAR',self.ranges.flatten(),display=False)
                angles = np.linspace(np.radians(0),np.radians(360),len(self.ranges)) + np.pi
                x = 200 + self.ranges * np.cos(angles)
                y = 200 + self.ranges * np.sin(angles)
                x = x.astype(np.uint8)
                y = y.astype(np.uint8)
                self.img_laser = np.zeros((400,400),dtype=np.uint8)
                self.img_laser[x,y] = 0xFF


    def read_cam(self):
        ''' Camera read thread
        '''
        while True:
            ret,frame = self.cap.read()
            if not ret:
                continue
            self.img_camera = frame;#cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


if __name__ == '__main__':
    gcs = GCS()
    gcs.mainloop()
