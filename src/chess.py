import cv2
import numpy as np
import time
from enum import Enum
from collections import Counter
import serial


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
    W = 1
    B = -1
    NULL = 0

class Board():
    def __init__(self):
        self.origin = [260,50]
        self.width = 800
        self.height = 800
        self.teamColorOffset = 10
        self.pieceColorDict = {
            Piece.K: ([127,0,0], [255,127,100]),
            Piece.Q: ([0,0,127], [127,127,255]),
            Piece.B: ([150,150,150], [255,255,255]),
            Piece.N: ([0,110,0], [150,255,150]),
            Piece.R: ([127,0,100], [255,180,200]),
            Piece.P: ([0,0,0], [100,100,100])
        }
        self.boardArray = np.zeros((8,8,2))
        self.outOfGameLoc = [0,400]
        self.actualWidth = 400 # mm
        self.actualHeight = 400 # mm

    def takeRawImage(self):
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1024)
        time.sleep(0.500)
        rawImage = cap.read()[1]
        enhancedImage = rawImage.copy()

        #Enhancing Saturation and reducing brightness to help identify colors
        hsvImg = cv2.cvtColor(rawImage,cv2.COLOR_BGR2HSV)

        #multiple by a factor to change the saturation
        hsvImg[...,1] = hsvImg[...,1]*1 #2.2

        #multiple by a factor of less than 1 to reduce the brightness 
        hsvImg[...,2] = hsvImg[...,2]*0.8 #0.6

        # Smooth out image to reduce noise
        smoothingSize = 6
        kernel = np.ones((smoothingSize,smoothingSize),np.float32)/(smoothingSize*smoothingSize)
        enhancedImage=cv2.filter2D(cv2.cvtColor(hsvImg,cv2.COLOR_HSV2BGR),-1,kernel)
        cv2.imshow('AnalyseSpot',enhancedImage)
        # cv2.imshow("Raw", rawImage)
        cv2.waitKey(0)
        return enhancedImage, rawImage

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
        # cv2.imshow("Circles", processedImage)
        # cv2.waitKey(0)
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
        pieceType = Piece.NULL.value
        typeColor = image[location[1], location[0]]
        # cv2.imshow('AnalyseSpot',image[location[1]-self.teamColorOffset:location[1]+self.teamColorOffset, location[0]-self.teamColorOffset:location[0]+self.teamColorOffset])
        # cv2.waitKey(0)
        pass
        for piece, pieceColor in self.pieceColorDict.items():
            if pieceColor[0][0] < typeColor[0] < pieceColor[1][0] and pieceColor[0][1] < typeColor[1] < pieceColor[1][1] and pieceColor[0][2] < typeColor[2] < pieceColor[1][2]:
                pieceType = piece.value
                break
        
        # Identify Team of piece
        bwImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        teamColor = bwImage[location[1]+self.teamColorOffset, location[0]+self.teamColorOffset]
        # cv2.imshow('AnalyseSpot',bwImage[location[1]-self.teamColorOffset:location[1]+self.teamColorOffset, location[0]-self.teamColorOffset:location[0]+self.teamColorOffset])
        # cv2.waitKey(0)
        whiteRange = [127, 255]
        blackRange = [0, 127]
        if (whiteRange[0] <= teamColor <= whiteRange[1]):
            team=Team.W.value
        elif (blackRange[0] <= teamColor < blackRange[1]):
            team=Team.B.value
        else:
            team = Team.NULL.value
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
        cv2.putText(image, Team(teamValue).name + Piece(pieceType).name, (orgX, orgY), font, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
        return image

    def generateBoard(self,rawImage, saturatedImage):
        locations, processedImage, grayImage = self.findPiecesLoc(rawImage)
        processedImage = self.drawGrid(processedImage)
        cv2.imshow("Griddy", processedImage)
        cv2.waitKey(0)
        for location in locations:
            # cv2.imshow('RawImage',rawImage)
            row, col, pieceType, team = self.identifyPiece(location, saturatedImage)
            self.updateBoardArray(row,col,pieceType,team)
            processedImage = self.addPiecesToImage(processedImage, row, col)
        cv2.imshow("Generated", processedImage)
        cv2.waitKey(0)
        return processedImage
            
    def convertToBoardCoord(self, row, col):
        # row and col should be numbers
        x = col*self.actualWidth/8+self.actualWidth/16
        y = row*self.actualHeight/8+self.actualHeight/16
        A = x
        B = y
        A16bit = A*80 #A mm * 80 step/mm 
        B16bit = B*80 #B mm * 80 step/mm
        return [A16bit, B16bit]

class Game():
    def __init__(self):
        # Setup Serial Communicator
        self.ser = serial.Serial ("COM12", 19200, timeout=None)    #Open port with baud rate
        self.moveArray = []

    def captureBoard(self):
        board = Board()
        saturatedImage, rawImage = board.takeRawImage()
        processedImage = board.generateBoard(rawImage, saturatedImage)
        return board, processedImage

    def detectMove(self, preBoard, postBoard):
        changeBoard = preBoard.boardArray - postBoard.boardArray
        changedIndices = changeBoard.nonzero()
        # changedIndices = [[1,2,1],[4,5,4],[1,1,1]]
        changedLocations = []
        for indic in range(len(changedIndices[0])):
            changedLocations.append([changedIndices[0][indic], changedIndices[1][indic]])
        dictChangedLocations = Counter(tuple(item) for item in changedLocations)
        changedProperties = set(tuple(changedIndices[2]))
        # Check if anything other than 2 locations changed or if team didn't change (both considered errors)
        if ((len(dictChangedLocations) != 2) or (0 not in changedProperties)):
            moveInput = input("Input your move in position moved from -> position moved to notation (ex. A2 A4): ")
            move_str = moveInput.replace(" ","")
            pass
        else:
            # Property Change:: prePos = 1: White - Null, postPos = -2: Black - White or -1: Null - White
            for location in changedLocations:
                if changeBoard[location[0]][location[1]][0] == 1:
                    prePos = BoardCols(location[1]+1).name + str(location[0] + 1)
                if changeBoard[location[0]][location[1]][0] == -2 or changeBoard[location[0]][location[1]][0] == -1:
                    postPos = BoardCols(location[1]+1).name + str(location[0] + 1)
            move_str = prePos + postPos
        return move_str #, team, piece

    def makeAIMove(self, ai_move, postBoard):
        # From ai_move castling move is bool x and y are 0 indexed
            # def __init__(self, xfrom, yfrom, xto, yto, castling_move):
            # self.xfrom = xfrom
            # self.yfrom = yfrom
            # self.xto = xto
            # self.yto = yto
            # self.castling_move = castling_move

        # Check if piece is being captured
        if postBoard.boardArray[ai_move.yto][ai_move.xto][0] == Team.W:
            edgeMove = True
            #Convert col and row to location
            A1, B1 = postBoard.convertToBoardCoord(ai_move.yto,ai_move.xto)
            self.moveArray.append(Move(A1, B1, 0)) # Start by moving to piece to be removed with no magnet
            A2, B2 = postBoard.convertToBoardCoord(ai_move.yto-0.5,ai_move.xto)
            self.moveArray.append(Move(A2, B2, 1)) # Move to forward edge of square
            A3, B3 = postBoard.convertToBoardCoord(ai_move.yto-0.5,-0.5)
            self.moveArray.append(Move(A3, B3, 1)) # Next move to OoB location with magnet

        # Next check is piece is castling
        if ai_move.castling_move:
            A4, B4 = postBoard.convertToBoardCoord(postBoard.outOfGameLoc[1],postBoard.outOfGameLoc[0])
            self.moveArray.append(Move(A4, B4, 1)) # Next move to OoB location with magnet            
            pass
        else:
            A5, B5 = postBoard.convertToBoardCoord(ai_move.yfrom,ai_move.xfrom)
            self.moveArray.append(Move(A5, B5, 0)) # Move to ai piece to move with no magnet
            if (postBoard.boardArray[ai_move.yfrom][ai_move.xfrom] == Piece.N):
                dX = ai_move.xto - ai_move.xfrom
                dY = ai_move.yto - ai_move.yfrom
                A6, B6 = postBoard.convertToBoardCoord(ai_move.yfrom+0.5*np.sign(dY),ai_move.xfrom+0.5*np.sign(dX))
                self.moveArray.append(Move(A6, B6, 1)) # Move to corner of square depending on quadrant
                if (dY > dX):
                    A7, B7 = postBoard.convertToBoardCoord(ai_move.yto,ai_move.xfrom+0.5*np.sign(dX))
                    self.moveArray.append(Move(A7, B7, 1)) # Move to ai piece to move with no magnet
                else:
                    A7, B7 = postBoard.convertToBoardCoord(ai_move.yto+0.5*np.sign(dY),ai_move.xto)
                    self.moveArray.append(Move(A7, B7, 1)) # Move to ai piece to move with no magnet
                # A8, B8 = postBoard.convertToBoardCoord(ai_move.yto,ai_move.xto)
                # self.moveArray.append(Move(A7, B7, 1)) # Move to ai piece to move with no magnet
            # else:      
            A8, B8 = postBoard.convertToBoardCoord(ai_move.yto, ai_move.xto)
            self.moveArray.append(Move(A8, B8, 1)) # Move to final AI location with magnet

        # Run trajectory planning function with above knowledge
        self.transferMovesToBoard()

    def planTrajectory(self, preLoc, postLoc, edgeMove, castling):
        # edgeMove is bool telling whether piece is moving on edges or not
        self.moveArray.append(Move(32000.0, 32000.0, 0))
        self.moveArray.append(Move(10000.0, 10000.0, 1))
        # self.moveArray.append(Move(10000.0, 10000.0, 2))
        self.transferMovesToBoard()
        pass

    def transferMovesToBoard(self):
        for move in self.moveArray:
            message = bytearray(move.moveMessage)
            self.ser.write(message)
            received_data = self.ser.read(7)              #read serial port
            receivedMessage = list(received_data)
            if (receivedMessage[1] != move.instruction):
                print("Error: Unexpected Movement Response")
                print(received_data)
                break
            print (received_data)                   #print received data
        if (len(self.moveArray) == move):
            print("AI move completed")
        self.moveArray = []
        pass

class Move():
    def __init__(self, x, y, instruction):
        self.instruction = instruction # 1 or 0 for on or off
        self.decoderByte = 0
        self.x16bit = round(x) # *0xFFFF/400*40/16
        self.y16bit = round(y)  #*0xFFFF/400*40/16
        self.xByte1 = self.x16bit>>8
        self.xByte2 = self.x16bit&0xFF
        self.yByte1 = self.y16bit>>8
        self.yByte2 = self.y16bit&0xFF
        if (self.xByte1 == 255):
            self.xByte1 = 0
            self.decoderByte |= 8
        if (self.xByte2 == 255):
            self.xByte2 = 0
            self.decoderByte |= 4
        if (self.yByte1 == 255):
            self.yByte1 = 0
            self.decoderByte |= 2
        if (self.yByte2 == 255):
            self.yByte2 = 0
            self.decoderByte |= 1 
        self.moveMessage = [255, self.instruction, self.xByte1, self.xByte2, self.yByte1, self.yByte2, self.decoderByte]       

if __name__ == "__main__":
    chessGame = Game()
    chessGame.planTrajectory(0,0,Piece.K,False)
    # runChessAI()
    # preBoard, preProcessedImage = chessGame.captureBoard()
    # cv2.imshow('PreBoard',preProcessedImage)
    # cv2.waitKey(0)
    # postBoard, postProcessedImage = chessGame.captureBoard()
    # cv2.imshow('PostBoard', postProcessedImage)
    # cv2.waitKey(0)
    # move_str = chessGame.detectMove(preBoard, postBoard)

    # prePosition, postPosition, team, piece = chessGame.detectMove(preBoard, postBoard)
    pass
    
