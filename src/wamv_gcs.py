import numpy as np
import socket
from threading import Thread
import tkinter as tk
import time
import logging
from datetime import datetime
from pathlib import Path

INC = 100
MAX = 500
MIN = -500

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

        # State
        self.last_pos = [0.,0.]
        self.last_hdg = 0.
        self.last_port = [0, 0]
        self.last_stbd = [0, 0]
        self.thrust_sp = 0
        self.rudder_sp = 0

    
    '''
    Utility Functions
    '''
    def set_thrust(self,increase=True):
        if increase: d=INC
        else: d=-INC
        self.thrust_sp = max(MIN,min(MAX,self.thrust_sp+d))
    

    def set_rudder(self,increase=True):
        if increase: d=INC
        else: d=-INC
        self.rudder_sp = max(MIN,min(MAX,self.rudder_sp+d))
    

    def stop(self):
        self.thrust_sp = 0
        self.rudder_sp = 0
        self.logger.info(f'WATCHDOG {self.thrust_sp:+04d} {self.rudder_sp:+04d}')
    

    def send_cmd(self):
        cmd = f'{self.thrust_sp:4d},{self.rudder_sp:4d},{self.thrust_sp:4d},{self.rudder_sp:4d}\n'
        try:
            pass
            #self.sock.sendto(cmd.encode(),('192.168.168.200', 6000))
            #self.logger.info('CMD: ' + cmd)
        except:
            print('Could not send cmd')

    def update(self):
        
        # Check for timeout
        if (time.time() - self.last_press) > 5:
            self.stop()
            self.last_press = time.time()
        
        # Send latest command
        self.send_cmd()
        
        # Update GUI
        
        self.timer = self.after(100, self.update)


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
            time.sleep(1)
            self.destroy()
        else:
            self.stop()
        self.logger.info(f'KEY:{event.keysym} {self.thrust_sp:+04d} {self.rudder_sp:+04d}')
        self.send_cmd()
        self.last_press = time.time()
    

    def read_sock(self):
        self.logger.info('Starting WAMV read thread')
        while True:
            pkt,addr = self.sock.recvfrom(4096)
            self.last_pkt = pkt
            self.logger.info(pkt.decode().strip())



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
