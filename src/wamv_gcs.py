import numpy as np
import socket
from threading import Thread
import tkinter as tk
import time
import logging
from datetime import datetime
from pathlib import Path
import pyproj

INC = 100
MAX = 700
MIN = -700
TIMEOUT = 60

class GCS(tk.Tk):
    ''' Ground Control System
            Extends a Tkinter window
    '''

    def __init__(self, *args, **kwargs):

        # Init Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_title("WAMV GCS")
        self.canvas = tk.Canvas(self, width=800, height=400, bg='black')
        self.canvas.grid(row=0,column=0,columnspan=4)
        self.enable = tk.Button(self, text='Enable', command = self.on_enable,bg='red')
        self.enable.grid(row=1,column=1,columnspan=2)
        self.stbd_slider = tk.Scale(self, from_=-1000, to=1000,orient=tk.HORIZONTAL)
        self.stbd_slider.grid(row=2,column=1)
        self.port_slider = tk.Scale(self, from_=-1000, to=1000,orient=tk.HORIZONTAL)
        self.port_slider.grid(row=2,column=2)
        # Logging, data collection
        logging.basicConfig(
            handlers=[logging.FileHandler(time.strftime("%Y%m%d_%H%M%S_wamv.log",time.localtime())),logging.StreamHandler()],
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] [%(module)s] %(message)s')
        self.logger = logging.getLogger()

        # Handle WAMV input
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #self.sock.settimeout(0)
            self.sock.bind(('192.168.168.77', 5000))
            self.sock_thread = Thread(target=self.read_sock, daemon=True)
            self.sock_thread.start()
        except:
            print('Could not open WAMV interface')

        # Events
        self.bind('<KeyPress>', self.key_press)
        self.last_press = time.time()
        self.timer = self.after(1000,self.update)

        self.proj = pyproj.Proj(proj='utm', zone=55, ellps='WGS84',preserve_units=True)

        # State
        self.enabled = False
        self.last_pos = [0.,0.]
        self.last_xy = [0., 0.]
        self.origin = [0., 0.]
        self.last_hdg = 0.
        self.last_port = [0, 0]
        self.last_stbd = [0, 0]
        self.pos_mode = False
        self.thrust_sp = 0
        self.rudder_sp = 0
        self.pos_sp = [0., 0.]

    
    '''
    Utility Functions
    '''
    def set_thrust(self,increase=True):
        self.pos_mode = False
        if increase: d=INC
        else: d=-INC
        self.thrust_sp = max(MIN,min(MAX,self.thrust_sp+d))
    

    def set_rudder(self,increase=True):
        self.pos_mode = False
        if increase: d=INC
        else: d=-INC
        self.rudder_sp = max(MIN,min(MAX,self.rudder_sp+d))
    

    def set_hold(self):
        # CHECK FOR VALIDITY 
        #   GeoFence?

        self.pos_mode = True
        self.pos_sp = self.last_pos.copy()


    def stop(self):
        self.pos_mode = False
        self.thrust_sp = 0
        self.rudder_sp = 0
        self.logger.info(f'WATCHDOG {self.thrust_sp:+04d} {self.rudder_sp:+04d}')
    

    def send_cmd(self):
        if not self.enabled:
            return
        if self.pos_mode:
            cmd = f'POSCMD,{self.pos_sp[0]},{self.pos_sp[1]}\n'
        else:
            cmd = f'{self.thrust_sp:4d},{self.rudder_sp:4d},{self.thrust_sp:4d},{self.rudder_sp:4d}\n'
        try:
            self.sock.sendto(cmd.encode(),('192.168.168.200', 6000))
        except:
            print('Could not send cmd')


    def update(self):
        
        # Check for timeout
        if (time.time() - self.last_press) > TIMEOUT:
            self.stop()
            self.last_press = time.time()
        
        # Send latest command
        self.send_cmd()
        
        # Update GUI
        dx = 400 + self.last_xy[0] - self.origin[0]
        dy = 200 + self.last_xy[1] - self.origin[1]
        self.canvas.create_oval(dx-5,dy-5,dx+5,dy+5,fill='blue',outline='black')
        
        self.timer = self.after(100, self.update)

    def on_enable(self):
        if self.enabled:
            self.enabled = False
            self.enable.configure(bg='red')
            self.enable.configure(text='Enable')
        else:
            self.enabled = True
            self.enable.configure(bg='green')
            self.enable.configure(text='Disable')
        self.logger.info(f'ENABLE: {self.enabled}')


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
        elif event.keysym == 'h':
            self.set_hold()
        elif event.keysym == 'q':
            self.stop()
            time.sleep(1)
            self.destroy()
        else:
            self.stop()
        if self.pos_mode:
            self.logger.info(f'KEY:{event.keysym} {self.pos_sp[0]} {self.pos_sp[1]}')
        else:
            self.logger.info(f'KEY:{event.keysym} {self.thrust_sp:+04d} {self.rudder_sp:+04d}')
        self.send_cmd()
        self.last_press = time.time()
    

    def read_sock(self):
        self.logger.info('Starting WAMV read thread')
        while True:
            pkt,addr = self.sock.recvfrom(4096)
            self.last_pkt = pkt.decode().strip()
            self.logger.info(self.last_pkt)
            fields = self.last_pkt.split(',')
            if fields[0] == 'N2K':
                self.last_pos = [float(fields[1]),float(fields[2])]
                self.last_hdg = float(fields[4])
                self.last_xy = self.proj(self.last_pos[1], self.last_pos[0])
                if self.origin == [0.,0.]:
                    self.origin = self.last_xy
            elif fields[0] == 'HLC':
                self.port_slider.set(int(fields[3]))
                self.stbd_slider.set(int(fields[4]))


if __name__ == '__main__':
    gcs = GCS()
    gcs.mainloop()
import numpy as np
import socket
from threading import Thread
import tkinter as tk
import time
import logging
from datetime import datetime
from pathlib import Path

INC = 30
MAX = 100
MIN = -100

class GCS(tk.Tk):
    ''' Ground Control System
            Extends a Tkinter window
    '''

    def __init__(self, *args, **kwargs):

        # Init Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_title("WAMV GCS")
        self.canvas = tk.Canvas(self, width=800, height=400, bg='black')
        self.canvas.pack()
        # Logging, data collection
        logging.basicConfig(
                handlers=[logging.FileHandler(f'{datetime.now():%Y%m%d_%H%M%S_wamv.log}'), logging.StreamHandler()],
                level=logging.INFO,
                format='%(asctime)s [%(levelname)s] [%(modules)s] %(message)s')
        self.logger = logging.getLogger()
        # Handle WAMV input
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, sock.SO_REUSEADDR, 1)
            self.sock.settimeout(0)
            self.sock_thread = Thread(target=self.read_sock, daemon=True)
            self.sock_thread.start()
        except:
            print('Could not open WAMV interface')

        # Events
        self.bind('<KeyPress>', self.key_press)
        self.last_press = time.time()
        self.timer = self.after(50,self.update)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        

        # State
        self.thrust = 0
        self.rudder = 0

    
    '''
    Utility Functions
    '''
    def set_thrust(self,increase=True):
        if increase: d=INC
        else: d=-INC
        self.thrust = max(MIN,min(MAX,self.thrust+d))
    def set_rudder(self,increase=True):
        if increase: d=INC
        else: d=-INC
        self.rudder = max(MIN,min(MAX,self.rudder+d))
