from threading import Thread
import time
import cv2

class CVTracker():
    def __init__(self, cam_url=2):

        self.camera_thread = Thread(target=self.read_cam, daemon=True)    
        self.cap = cv2.VideoCapture(cam_url)
        self.img_frame = None
        self.tracker = cv2.TrackerKCF_create()
        self.running = False


    def read_cam(self):
        while self.running:
            ret,frame = self.cap.read()
            if not ret:
                continue
            self.img_frame = frame


    def run(self):
        self.running = True

        if self.cap.isOpened():
            self.camera_thread.start()

        while self.running:
            if self.img_frame is not None:
                cv2.imshow("CAM", self.img_frame)
                key = cv2.waitKey(10) & 0xFF
                if key == ord('q'):
                    self.running = False
                    break
                elif key == ord('r'):
                    print('Selecting ROI')
                    roi = cv2.selectROI("Select Object", self.img_frame)
                    self.tracker.init(self.img_frame, roi)
                    print(roi)
                try:
                    print(self.tracker.update(self.img_frame))
                except:
                    print('bad track')
        time.sleep(.1)
        cv2.destroyAllWindows()
    



if __name__ == '__main__':
    tracker = CVTracker()
    tracker.run()