import cv2
import numpy as np
import time
from enum import Enum

class Piece(Enum):
    K = 1
    Q = 2
    B = 3
    N = 4
    R = 5
    P = 6
    NULL = -1

class BoardCols(Enum):
    A = 1
    B = 2
    C = 3
    D = 4
    E = 5
    F = 6
    G = 7
    H = 8

class Team(Enum):
    W = 0
    B = 1
    NULL = -1

def setupCamera():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
    time.sleep(1.000)
    return cap

def takeRawImage(cap):
    return (cap.read()[1])

class Board():
    def __init__(self):
        self.origin = [320,80]
        self.width = 750
        self.height = 750
        self.teamColorOffset = 10
        self.pieceColorDict = {
            Piece.K: ([140,0,0], [255,150,127]),
            Piece.Q: ([0,0,127], [120,127,255]),
            Piece.B: ([100,127,127], [200,255,255]),
            Piece.N: ([0,127,0], [160,225,127]),
            Piece.R: ([120,0,127], [255,127,255]),
            Piece.P: ([155,150,0], [255,255,127])
        }
        self.boardArray = [
            [[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL]],
            [[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL]],
            [[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL]],
            [[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL]],
            [[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL]],
            [[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL]],
            [[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL]],
            [[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL],[Team.NULL, Piece.NULL]]
        ]

    def findPiecesLoc(self, image):
        # Convert image to grayscale
        processedImage = image.copy()
        gray = cv2.GaussianBlur(cv2.cvtColor(processedImage, cv2.COLOR_BGR2GRAY),(7,7),1.9)
        # Use Hough Circle 
        circ = cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT, 1.0, 20, param1=80, param2=35, minRadius=15, maxRadius=30)

        if circ is not None:
            circ = np.uint16(np.around(circ))[0,:]
            # print(circ)
            for c in circ:
                cv2.circle(gray, (c[0], c[1]), c[2], (0, 255, 0), 3)
                cv2.circle(gray, (c[0], c[1]), 1, (0, 0, 255), 5)
                cv2.circle(processedImage, (c[0], c[1]), c[2], (0, 255, 0), 2)
                cv2.circle(processedImage, (c[0], c[1]), 1, (0, 0, 255), 3)
                cv2.circle(processedImage, (c[0]+self.teamColorOffset, c[1]+self.teamColorOffset), 1, (0, 0, 0), 1)
        return circ, processedImage, gray

    def drawGrid(self,image):
        rows = 8
        cols = 8
        dy, dx = self.height / rows, self.width / cols
        color=(0, 0, 0)
        thickness = 3

        # draw vertical lines
        for x in np.linspace(start=self.origin[0], stop=self.width + self.origin[0], num=cols+1):
            x = int(round(x))
            cv2.line(image, (x, self.origin[1]), (x, self.height + self.origin[1]), color=color, thickness=thickness)

        # draw horizontal lines
        for y in np.linspace(start=self.origin[1], stop=self.height + self.origin[1], num=rows+1):
            y = int(round(y))
            cv2.line(image, (self.origin[0], y), (self.width + self.origin[0], y), color=color, thickness=thickness)
        return image

    def identifyPiece(self,location,image):
        adjustedLoc = [location[1] - self.origin[1], location[0] - self.origin[0]]
        # Find Row and Column of Piece
        col = BoardCols(int(adjustedLoc[1] / (self.width/8) + 1))
        row = int(adjustedLoc[0] / (self.height/8) + 1)
        # Find Type of Piece
        # cv2.imshow('AnalyseSpot',contrastImage)
        # cv2.waitKey(0)
        pieceType = Piece.NULL
        typeColor = image[location[1], location[0]]
        # cv2.imshow('AnalyseSpot',image[location[1]-self.teamColorOffset:location[1]+self.teamColorOffset, location[0]-self.teamColorOffset:location[0]+self.teamColorOffset])
        # cv2.waitKey(0)
        pass
        for piece, pieceColor in self.pieceColorDict.items():
            if pieceColor[0][0] < typeColor[0] < pieceColor[1][0] and pieceColor[0][1] < typeColor[1] < pieceColor[1][1] and pieceColor[0][2] < typeColor[2] < pieceColor[1][2]:
                pieceType = piece
                break
        
        # Identify Team of piece
        bwImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        teamColor = bwImage[location[1]+self.teamColorOffset, location[0]+self.teamColorOffset]
        # cv2.imshow('AnalyseSpot',bwImage[location[1]-self.teamColorOffset:location[1]+self.teamColorOffset, location[0]-self.teamColorOffset:location[0]+self.teamColorOffset])
        # cv2.waitKey(0)
        whiteRange = [127, 255]
        blackRange = [0, 127]
        if (whiteRange[0] <= teamColor <= whiteRange[1]):
            team=Team.W
        elif (blackRange[0] <= teamColor < blackRange[1]):
            team=Team.B
        else:
            team = Team.NULL
            print("Team not Recognized")
        return row,col,pieceType,team

    def updateBoardArray(self,row,col,pieceType,team):
        self.boardArray[row-1][BoardCols(col).value-1] = [team, pieceType]

    def addPiecesToImage(self, image, row, col):
        font = cv2.FONT_HERSHEY_SIMPLEX
        teamValue = self.boardArray[row-1][BoardCols(col).value-1][0]
        pieceType = self.boardArray[row-1][BoardCols(col).value-1][1]
        orgX = round((self.origin[0] + (BoardCols(col).value-1)*self.width/8 + 5)) #  + self.width/16
        orgY = round((self.origin[1] + (row-1)*self.height/8+self.height/8-5)) # + self.height/16
        cv2.putText(image, teamValue.name + pieceType.name, (orgX, orgY), font, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
        return image

    def generateBoard(self,rawImage):
        locations, processedImage, grayImage = self.findPiecesLoc(rawImage)
        processedImage = self.drawGrid(processedImage)
        for location in locations:
            # cv2.imshow('RawImage',rawImage)
            row, col, pieceType, team = self.identifyPiece(location, rawImage)
            self.updateBoardArray(row,col,pieceType,team)
            processedImage = self.addPiecesToImage(processedImage, row, col)
        return processedImage



if __name__ == "__main__":
    camera = setupCamera()
    board = Board()
    rawImage = takeRawImage(camera)
    # locations, image, grayImage = board.findPiecesLoc(rawImage)
    # print(locations)
    # for location in locations:
    #     board.identifyPiece(location, rawImage)
    # # board.identifyPiece(locations[0], rawImage)
    # image = board.drawGrid(image)
    # board, image = mapBoard(locations, image)
    processedImage = board.generateBoard(rawImage)
    cv2.imshow('ProcessedBoard',processedImage)
    pass
    cv2.waitKey(0)
    pass
    
