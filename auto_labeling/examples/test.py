import cv2 as cv
import numpy as np

feature = np.zeros( (800, 800), dtype=np.uint8)
cv.imshow("preview", feature )
cv.waitKey()
print(cv.__version__)