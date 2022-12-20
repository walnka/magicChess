import chess
import cv2


import time 

# cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
time.sleep(1.000)

chessBoard = chess.Board()
chessGame = chess.Game()


while(True):
    board, processedImage = chessGame.captureBoard()
    # img = cap.read()
    # img = cv2.GaussianBlur(img[1], (7, 7), 1.5)
    # # img = cv2.medianBlur(img,5)
    # resized = img  #cv2.cvtColor(img[1], cv2.COLOR_GRAY2BGR)
    # circ = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1.3, 30, param1=20, param2=55, minRadius=10, maxRadius=30)

    # gray = cv2.medianBlur(cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2GRAY),5)
    cv2.imshow('video',processedImage)
    if cv2.waitKey(1)==27:# esc Key 
        break
    while(1):
        pass

# cap.release()
cv2.destroyAllWindows()