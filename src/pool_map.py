import numpy as np
import cv2

map = np.zeros((310,210),dtype=np.uint8)

pool_points = np.array([[0,0],[0,289],[200,289],[200,218],[144,218],[144,49],[200,49],[200,0]],dtype=np.int32)

pool_points = pool_points + (5,5)

cv2.polylines(map,[pool_points.reshape((-1,1,2))],True,255,1)
map = cv2.GaussianBlur(map,(11,11),0)
map = cv2.normalize(map,None,0,255,cv2.NORM_MINMAX)

cv2.imwrite('survival_pool.png',map)
cv2.imshow('map',map)
cv2.waitKey(0)
cv2.destroyAllWindows()

