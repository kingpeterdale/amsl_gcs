import numpy as np
import pandas as pd
import cv2

class LaserLocator():
    def __init__(self, init=(0.,0.,0.)):
        
        # Static Base Map
        self.static_map = cv2.imread('/home/peter/code/AMSL/amsl_gcs/src/survival_pool.png',cv2.IMREAD_GRAYSCALE)

        # Laser Scans
        self.scan_angles = np.linspace(np.radians(0),np.radians(360),720)
        self.laser_file = open('/home/peter/code/AMSL/amsl_gcs/src/logs/20251119_145433/gcs_145433.log')

        # State Estimate
        self.dx = init[0]
        self.dy = init[1]
        self.dh = init[2]


    def get_next_scan(self):
        for line in self.laser_file:
            fields = line.split(',')
            if len(fields) > 4 and fields[3] == 'LIDAR':
                scan = np.array([int(f) for f in fields[4:]])
                return scan
    

    def start_grid_based(self,local_search_window=(5,5,5)):
        '''
        For each scan, searches a local grid to find best match.
        local grid is relative to current estimate.
        Initial guess must be provided
        
        :param local_search_window: size of local area to search
        '''
        grid_x = np.arange(self.dx-local_search_window[0],self.dx+local_search_window[0]+1)
        grid_y = np.arange(self.dy-local_search_window[1],self.dy+local_search_window[1]+1)
        grid_h = np.arange(self.dh-local_search_window[2],self.dh+local_search_window[2]+1)
        max_score = 0.0
        best_estimate = (0.,0.,0.)

        scan = self.get_next_scan()
        while True:
            for gx in grid_x:
                for gy in grid_y:
                    for gh in grid_h:
                        laser_grid = np.zeros_like(self.static_map)
                        x = gx + scan * np.cos(np.radians(gh) + self.scan_angles)
                        y = gy + scan * np.sin(np.radians(gh) + self.scan_angles)
                        x = np.clip(x,0,209)
                        y = np.clip(y,0,309)
                        laser_grid[y.astype(np.uint16),x.astype(np.uint16)] = 1.0
                        score = np.multiply(self.static_map, laser_grid).sum()
                        if score > max_score:
                            best_estimate = (gx,gy,gh)
                            max_score = score

            laser_grid = np.zeros_like(self.static_map)
            (self.dx,self.dy,self.dh) = best_estimate
            self.dh = (self.dh+180)%360 - 180

            x = self.dx + scan * np.cos(np.radians(self.dh) + self.scan_angles)
            y = self.dy + scan * np.sin(np.radians(self.dh) + self.scan_angles)
            x = np.clip(x,0,209)
            y = np.clip(y,0,309)
            laser_grid[y.astype(np.uint16),x.astype(np.uint16)] = 1.0
            combined = self.static_map + 255*laser_grid
            cv2.imshow('EST',cv2.resize(combined,None,fx=2,fy=2))

            print(best_estimate, max_score)


            key = cv2.waitKey(5)
            if key == ord('q'):
                cv2.destroyAllWindows()
                break
            else:
                grid_x = np.arange(self.dx-local_search_window[0],self.dx+local_search_window[0]+1)
                grid_y = np.arange(self.dy-local_search_window[1],self.dy+local_search_window[1]+1)
                grid_h = np.arange(self.dh-local_search_window[2],self.dh+local_search_window[2]+1)
                max_score = 0.0
                best_estimate = (0.,0.,0.)
                scan = self.get_next_scan()

                    
        

    def start_manual(self):
        scan = self.get_next_scan()
        print(scan)
        

        max_score = 0.
        while True:
            #cv2.imshow('Map',self.static_map)
            laser_grid = np.zeros_like(self.static_map)
            x = self.dx + scan * np.cos(np.radians(self.dh) + self.scan_angles)
            y = self.dy + scan * np.sin(np.radians(self.dh) + self.scan_angles)
            x = np.clip(x,0,209)
            y = np.clip(y,0,309)
            laser_grid[y.astype(np.uint16),x.astype(np.uint16)] = 1.0
            score = np.multiply(self.static_map, laser_grid).sum()
            max_score = max(max_score, score)
            
            combined = self.static_map + 255*laser_grid
            cv2.imshow('MAP',cv2.resize(combined,None,fx=2,fy=2))

            key = cv2.waitKey(0)
            if key == ord('q'):
                cv2.destroyAllWindows()
                break
            elif key == ord('n'):
                scan = self.get_next_scan()
                max_score = 0.
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
                self.dh += 1
            elif key == ord('e'):
                self.dh -= 1
            self.dh = (self.dh+180)%360 - 180
            print(f'{self.dx} {self.dy} {self.dh} {score/max_score:0.3f} {score:0.3f}')



if __name__ == '__main__':
    locater = LaserLocator(init=(105., 76., -111.))
    #locater.start_manual()
    locater.start_grid_based()
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
