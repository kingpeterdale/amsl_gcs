import numpy as np
import serial
from threading import Thread
import tkinter as tk
import time

MULT = 2.5

INC = 30
MAX = 100
MIN = -100

class GCS(tk.Tk):
    def __init__(self, *args, **kwargs):
        
        # Init Tk
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_title("Laser Bot GCS")
        self.canvas = tk.Canvas(self, bg='black', height=MULT*400, width=MULT*400)
        self.canvas.pack()

        # Handle SiK Radio
        self.sik_port = serial.Serial('/dev/serial/by-id/usb-FTDI_FT231X_USB_UART_D30GKCRB-if00-port0',57600,timeout=None)
        self.sik_thread = Thread(target=self.read_sik, daemon=True)
        self.sik_thread.start()

        # Events
        self.bind('<KeyPress>', self.key_press)
        self.last_press = time.time()
        self.timer = self.after(500,self.update)

        # State
        self.thrust = 0
        self.rudder = 0


    def set_thrust(self,increase=True):
        if increase: d=INC
        else: d=-INC
        self.thrust = max(MIN,min(MAX,self.thrust+d))
    def set_rudder(self,increase=True):
        if increase: d=INC
        else: d=-INC
        self.rudder = max(MIN,min(MAX,self.rudder+d))
    def stop(self):
        self.thrust = 0
        self.rudder = 0
        self.send_cmd()
    def send_cmd(self):
        cmd = f'$CMD,{self.thrust:+04d},{self.rudder:+04d}\n'
        print(cmd)
        self.sik_port.write(cmd.encode())
    def update(self):
        if (time.time() - self.last_press) > 5:
            self.stop()
            self.last_press = time.time()
        self.timer = self.after(500,self.update)


    def key_press(self, event):
        self.last_press = time.time()
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
            exit()
        else:
            self.stop()
        self.send_cmd()
    

    def read_sik(self):
        while True:
            pkt = self.sik_port.read_until(b'\xFF',1024)
            if len(pkt) > 1:
                timestamp =pkt[:15]
                self.ranges = np.frombuffer(pkt[15:-1],dtype=np.uint8)
                angles = np.linspace(np.radians(0),np.radians(360),len(self.ranges)) + np.pi
                
                self.canvas.delete('all')
                self.canvas.create_oval(MULT*200-MULT*100,MULT*200-MULT*100,MULT*200+MULT*100,MULT*200+MULT*100,fill='black',outline='blue')
                self.canvas.create_oval(MULT*200-MULT*50,MULT*200-MULT*50,MULT*200+MULT*50,MULT*200+MULT*50,fill='black',outline='blue')
                self.canvas.create_oval(MULT*200-MULT*10 ,MULT*200-MULT*10 ,MULT*200+MULT*10 ,MULT*200+MULT*10 ,fill='black',outline='green')
                self.canvas.create_line(MULT*200,MULT*200,MULT*200,MULT*200-MULT*10,fill='green')
                for i in range(len(self.ranges)):
                    dy = MULT*200 + MULT*self.ranges[i] * np.cos(angles[i])
                    dx = MULT*200 + MULT*self.ranges[i] * np.sin(angles[i])
                    self.canvas.create_oval(dx-1,dy-1,dx+1,dy+1,fill='red',outline='black')

if __name__ == '__main__':
    gcs = GCS()
    gcs.mainloop()
