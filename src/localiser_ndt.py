import numpy as np
import pandas as pd
import cv2

import particle_filter_xyh as pf
from particle_filter_xyh import X,Y,H,W,V

class LaserLocator():
    def __init__(self, init=(0.,0.,0.,0.)):
        
        # Static Base Map
        self.static_map = cv2.imread('/home/peter/code/AMSL/amsl_gcs/src/survival_pool.png',cv2.IMREAD_GRAYSCALE)

        # Laser Scans
        self.scan_angles = np.linspace(np.radians(0),np.radians(360),720)
        self.laser_file = open('/home/peter/code/AMSL/amsl_gcs/src/logs/20251119_145433/gcs_145433.log')

        # State Estimate
        self.dx = init[0]
        self.dy = init[1]
        self.dh = init[2]
        self.dv = init[3]


    def get_next_scan(self):
        for line in self.laser_file:
            fields = line.split(',')
            if len(fields) > 4 and fields[3] == 'LIDAR':
                scan = np.array([int(f) for f in fields[4:]])
                filt = np.argwhere(scan>1.)
                return scan[filt], self.scan_angles[filt]
    

    def start_particle_filter(self, std=(10,10,10,10)):
        '''
        Utilise a particle filter to estimate the position starting from
        the initial state
        
        :param std: standard deviation of initial particle distribution
        '''
        particles = pf.gen_gaussian_particles(num=5000,std=std,init=(self.dx, self.dy, self.dh, self.dv))
        
        scan,angles = self.get_next_scan()
        while True:

            output_grid = np.zeros_like(self.static_map)
            

            # Calculate likelihood
            likelihood = []
            for p in particles:
                x = p[X] + scan * np.cos(np.radians(p[H]) + angles)
                y = p[Y] + scan * np.sin(np.radians(p[H]) + angles)
                x = np.clip(x,0,499)
                y = np.clip(y,0,499)
                #laser_grid = np.zeros_like(self.static_map)
                #laser_grid[y.astype(np.uint16), x.astype(np.uint16)] = 255
                #laser_corners = cv2.cornerHarris(laser_grid, 10, 3, 0.04)
                score = self.static_map[y.astype(np.uint16), x.astype(np.uint16)].sum()**2
                #score = np.multiply(self.static_map, laser_corners).sum()**2
                likelihood.append(score)

                
                try:
                    output_grid[p[X].astype(np.uint16),p[Y].astype(np.uint16)] = 128
                except:
                    pass
            # Update Step
            particles = pf.update_particles(particles, np.array(likelihood))

            # Estimate
            estimate, var = pf.estimate(particles)
            self.dx = estimate[X]
            self.dy = estimate[Y]
            self.dh = estimate[H]
            self.dv = estimate[V]

            
            self.dh = (self.dh+180)%360 - 180
            x = self.dx + scan * np.cos(np.radians(self.dh) + angles)
            y = self.dy + scan * np.sin(np.radians(self.dh) + angles)
            x = np.clip(x,0,499)
            y = np.clip(y,0,499)
            output_grid[y.astype(np.uint16),x.astype(np.uint16)] = 255
            combined = self.static_map + output_grid
            cv2.imshow('EST',cv2.resize(combined,None,fx=2,fy=2))

            print(estimate)

            # Resample
            particles = pf.resample_particles(particles)

            # Predict Step
            particles = pf.predict_particles(particles)
            particles = pf.jitter_particles(particles)



            key = cv2.waitKey(0)
            if key == ord('q'):
                cv2.destroyAllWindows()
                break
            else:
                scan,angles = self.get_next_scan()
                if scan is None:
                    cv2.destroyAllWindows()
                    break

                    
        

    def start_manual(self):
        scan,angles = self.get_next_scan()
        print(scan)
        

        max_score = 0.
        while True:
            #cv2.imshow('Map',self.static_map)
            x = self.dx + scan * np.cos(np.radians(self.dh) + angles)
            y = self.dy + scan * np.sin(np.radians(self.dh) + angles)
            x = np.clip(x,0,500)
            y = np.clip(y,0,500)

            laser_grid = np.zeros_like(self.static_map)
            laser_grid[y.astype(np.uint16), x.astype(np.uint16)] = 1
            laser_corners = cv2.cornerHarris(laser_grid, 10, 3, 0.04)
            laser_corners[laser_corners>0.5*laser_corners.max()]=1
            score = np.multiply(self.static_map, laser_corners).sum()**2

            #laser_grid[y.astype(np.uint16),x.astype(np.uint16)] = 1.0
            #score = np.multiply(self.static_map, laser_grid).sum()
            max_score = max(max_score, score)
            
            combined = np.multiply(self.static_map,laser_corners)
            combined  = cv2.normalize(combined,None,0,255,cv2.NORM_MINMAX)
            combined = 254 * laser_corners
            cv2.imshow('MAP',cv2.resize(combined,None,fx=2,fy=2))

            key = cv2.waitKey(0)
            if key == ord('q'):
                cv2.destroyAllWindows()
                break
            elif key == ord('n'):
                scan,angles = self.get_next_scan()
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
    locater = LaserLocator(init=(199., 169., -110., 0.))
    #locater.start_manual()
    locater.start_particle_filter(std=(1,1,1,1))
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
