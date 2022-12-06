import cv2 as cv
import numpy as np
import time

img = cv.imread("colorTest.jpg", 0)
img = cv.GaussianBlur(img, (7, 7), 1.5)

cimg = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
circles = cv.HoughCircles(img, cv.HOUGH_GRADIENT, 1.3, 30, param1=20, param2=55, minRadius=10, maxRadius=30)

circles = np.uint16(np.around(circles))

for c in circles[0, :]:
    cv.circle(cimg, (c[0], c[1]), c[2], (0, 255, 0), 3)
    cv.circle(cimg, (c[0], c[1]), 1, (0, 0, 255), 5)

cv.imshow("cimg", cimg)
cv.waitKey(0)
# cv.imwrite(“houghcircle.png”, cimg)


