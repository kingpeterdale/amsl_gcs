from threading import Thread
from queue import Queue, Empty, Full
import time
import cv2

class CVTracker():
    def __init__(self, cam_url=2):

        self.process_thread = Thread(target=self.processing, daemon=True)
        self.process_queue =  Queue(1)
        self.tracker = cv2.TrackerKCF_create()
        self.running = False


    def processing(self):
        print("Processing thread starting")
        while self.running:
            try:
                frame = self.process_queue.get_nowait()    
                cv2.imshow("Tracker", cv2.resize(frame,None,None,0.5,0.5))
                key = cv2.waitKey(10) & 0xFF
                if key == ord('q'):
                    self.running = False
                    break
                elif key == ord('r'):
                    print('Selecting ROI')
                    roi = cv2.selectROI("Select Object", frame)
                    self.tracker.init(frame, roi)
                    print(roi)
                try:
                    print(self.tracker.update(frame))
                except:
                    print('bad track')
            except Empty:
                pass
                time.sleep(0.01)
            except Exception as e:
                print(e)
                print("Terminating processing thread")
                self.running = False
        
        time.sleep(.1)
        cv2.destroyAllWindows()
        print("Processing thread ending")


    def update(self, img):
        try:
            self.process_queue.put_nowait(img)
        except Full:
            # Do nothing, we lose frame
            pass
        except Exception as e:
            print(e)

    def start(self):
        self.running = True
        if not self.process_thread.is_alive():
            self.process_thread.start()

    def stop(self):
        self.running = False
        time.sleep(1)

    



if __name__ == '__main__':
    tracker = CVTracker()
    tracker.start()

    from glob import glob
    files = sorted(glob("/media/peter/DATATX/20251126_111033/*.jpg"))
    for f in files:
        img = cv2.imread(f)
        tracker.update(img)