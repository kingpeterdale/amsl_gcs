import numpy as np
import cv2

map = np.zeros((500,500),dtype=np.uint8)

cv2.line(map,(0,0),(0,289),255,1)
cv2.line(map,(0,289),(200,289),255,1)
cv2.line(map,(200,218),(144,218),255,1)
cv2.line(map,(144,218),(144,49),255,1)
cv2.line(map,(144,49),(200,49),255,1)
cv2.line(map,(200,0),(0,0),255,1)

M = np.float32([[1,0,100],[0,1,100]])
map = cv2.warpAffine(map,M,(map.shape[1],map.shape[0]))
map = cv2.GaussianBlur(map,(1,1),1)
map = cv2.normalize(map,None,0,255,cv2.NORM_MINMAX)

cv2.imwrite('/home/peter/code/AMSL/amsl_gcs/src/survival_pool.png',map)
cv2.imshow('map',map)
cv2.waitKey(0)
cv2.destroyAllWindows()

