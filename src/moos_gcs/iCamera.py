#!/usr/bin/env python3

from threading import Thread
import time
import cv2

import pymoos

PERIOD = 0.5 # camera period in seconds

class iCamera(pymoos.comms):

    def __init__(self, moos_community, moos_port):
        super(iCamera, self).__init__()
        self.server = moos_community
        self.port = moos_port
        self.name = 'iCamera'

        self.set_on_connect_callback(self.on_connect)
        self.set_on_mail_callback(self.on_mail)

        self.cap = cv2.VideoCapture(2)
        self.img_frame = None
        self.running = True

        self.last_update = pymoos.time()

        self.run(self.server, self.port, self.name)


    def on_connect(self):
        self.register("CAM_CMD", 0)
        return True


    def on_mail(self):
        for msg in self.fetch():
            if msg.key() == "CAM_CMD":
                if msg.string() == "START":
                    self.running = True
                elif msg.string() == "STOP":
                    self.running = False
        return True
    

    def cam_loop(self):
        ''' Thread to read camera images as fast as possible '''
        while True:
            if self.running:
                ret,frame = self.cap.read()
                if ret:
                    self.img_frame = frame
            else:
                time.sleep(.1)


    def run_loop(self):
        ''' Main loop. Sends out notification based on set PERIOD'''
        Thread(target=self.cam_loop, daemon=True).start()
        while True:
            shape = self.img_frame.shape
            self.notify('CAM_SHAPE',f'{shape[0]},{shape[1]},{shape[2]}',pymoos.time())
            self.notify_binary('CAM_IMG', self.img_frame.tobytes(),pymoos.time())
            self.last_update = pymoos.time()
            time.sleep(PERIOD)


def main():
    icam = iCamera('localhost', 9000)
    try:
        icam.run_loop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)


if __name__=="__main__":
    main()