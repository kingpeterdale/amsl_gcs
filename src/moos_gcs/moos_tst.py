#!/usr/bin/env python3

import cv2
import numpy as np

import pymoos
import time

# A super simple example:
# a) we make a comms object, and run it
# b) we enter a forever loop in which we both send notifications
#    and check and print mail (with fetch)
# c) the map(lambda,,,) bit simply applies trace() to every message to print
#    a summary of the message.

comms = pymoos.comms()

rows = 1080
cols = 1920
chan = 3
img = None

def on_connect():
    comms.register('CAM_SHAPE',0)
    comms.register('CAM_IMG',0)
    return True


def on_mail():
    global rows, cols, chan, img
    msgs = comms.fetch()
    for msg in msgs:
        if msg.key() == "CAM_SHAPE":
            fields = msg.string().split(',')
            rows = int(fields[0])
            cols = int(fields[1])
            chan = int(fields[2])
        elif msg.key() == "CAM_IMG":
            img = np.frombuffer(msg.binary_data(),dtype=np.uint8).reshape((rows,cols,chan))
    return True



def main():
    # my code here
    comms.set_on_connect_callback(on_connect)
    comms.set_on_mail_callback(on_mail)
    comms.run('localhost',9000,'LISTENER')
    
    try:
        while True:
            if img is not None:
                cv2.imshow("MOOS_CAM", img)
                key = cv2.waitKey(10) & 0xFF
                if key == ord('q'):
                    break
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
    cv2.destroyAllWindows()
        

if __name__ == "__main__":
    main()    