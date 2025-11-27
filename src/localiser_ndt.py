import numpy as np
import pandas as pd
import cv2

class LaserLocator():
    def __init__(self):
        
        # Static Base Map
        self.static_map = cv2.imread('survival_pool.png',cv2.IMREAD_GRAYSCALE)

        # Laser Scans
        self.scan_angles = np.linspace(np.radians(0),np.radians(360),720)
        self.laser_file = open('/home/peter/code/AMSL/amsl_gcs/src/logs/20251119_145433/gcs_145433.log')

        # State Estimate
        self.dx = 0
        self.dy = 0
        self.dh = 0

    def get_next_scan(self):
        for line in self.laser_file:
            fields = line.split(',')
            if len(fields) > 4 and fields[3] == 'LIDAR':
                scan = np.array([int(f) for f in fields[4:]])
                return scan
    

    def start_manual(self):
        scan = self.get_next_scan()
        print(scan)
            
        while True:
            #cv2.imshow('Map',self.static_map)
            laser_grid = np.copy(self.static_map)
            x = self.dx + scan * np.cos(self.dh + self.scan_angles)
            y = self.dy + scan * np.sin(self.dh + self.scan_angles)
            x = np.clip(x,0,209)
            y = np.clip(y,0,309)
            print(y.max())
            laser_grid[y.astype(np.uint16),x.astype(np.uint16)] = 0xFF
            cv2.imshow('MAP',cv2.resize(laser_grid,None,fx=2,fy=2))

            key = cv2.waitKey(0)
            if key == ord('q'):
                cv2.destroyAllWindows()
                break
            elif key == ord('n'):
                scan = self.get_next_scan()
                print(scan)
            elif key == 82:
                self.dy += 1
            elif key == 84:
                self.dy -= 1
            elif key == 83:
                self.dx += 1
            elif key == 81:
                self.dx -= 1
            elif key == ord('r'):
                self.dh += np.radians(1)
            elif key == ord('e'):
                self.dh -= np.radians(1)
            self.dh = self.dh
            print(self.dx,self.dy,self.dh)



if __name__ == '__main__':
    locater = LaserLocator()
    locater.start_manual()
'''    

    with open('/home/peter/code/AMSL/amsl_gcs/src/logs/20251119_145433/gcs_145433.log') as logfile:
        for line in logfile:
            fields = line.split(',')
            if len(fields) > 4 and fields[3] == 'LIDAR':
                scan = np.array([int(f)/10. for f in fields[4:]])
                x = scan * np.cos(angles)
                y = scan * np.sin(angles)
                grid = np.zeros((320,320),dtype=np.uint8)
                grid[x.astype(np.uint8),y.astype(np.uint8)] = 0xFF
                
                df = pd.DataFrame({'x':x, 'y':y, 'x_sub':x.round(0),'y_sub':y.round()})
                m = df.groupby(['x_sub','y_sub']).mean()
                v = df.groupby(['x_sub','y_sub']).var()
                print(m)
                print(v)
                exit()
                cv2.imshow('grid',mean)
                key = cv2.waitKey(0)
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    break
    '''