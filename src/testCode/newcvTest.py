import cv2
import numpy as np
import time 

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
time.sleep(1.000)

# time.sleep(1)
# width = 1920
# height = 1080
# dim = (width, height)
# while(True):
    # img = cap.read()
    # img = cv2.GaussianBlur(img[1], (7, 7), 1.5)
    # # img = cv2.medianBlur(img,5)
    # resized = img  #cv2.cvtColor(img[1], cv2.COLOR_GRAY2BGR)
    # circ = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1.3, 30, param1=20, param2=55, minRadius=10, maxRadius=30)

    # gray = cv2.medianBlur(cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2GRAY),5)
gray = cv2.GaussianBlur(cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2GRAY),(7,7),1.9)
resized = gray
circ = cv2.HoughCircles(resized,cv2.HOUGH_GRADIENT, 1.0, 20, param1=80, param2=35, minRadius=15, maxRadius=30)
cv2.imshow('video',resized)
if circ is not None:
    circ = np.uint16(np.around(circ))[0,:]
    print(circ)
    for c in circ:
        cv2.circle(resized, (c[0], c[1]), c[2], (0, 255, 0), 3)
        cv2.circle(resized, (c[0], c[1]), 1, (0, 0, 255), 5)
    cv2.imshow('video',resized)
    # if cv2.waitKey(1)==27:# esc Key 
    #     break
    # while(1):
    #     pass
cv2.waitKey(0)

# cap.release()
# cv2.destroyAllWindows()