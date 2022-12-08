## Slightly modified from https://github.com/Dirk94/ChessAI ##
import board, pieces, ai, chess, cv2

# Returns a move object based on the users input. Does not check if the move is valid.
def get_user_move(attempt):
    ## Willem Change: run vision and chess.py methods to get user move ##
    if attempt == 1:
        preBoard, preProcessedImage = chessGame.captureBoard()
        cv2.imshow('PreBoard',preProcessedImage)
        cv2.waitKey(0)
        input("Make your move now, press enter when finished")
        postBoard, postProcessedImage = chessGame.captureBoard()
        cv2.imshow('PostBoard', postProcessedImage)
        cv2.waitKey(0)
        move_str = chessGame.detectMove(preBoard, postBoard)
    else:
        print("Example Move: A2 A4")
        move_str = input("Your Move: ")
        move_str = move_str.replace(" ", "")

    try:
        xfrom = letter_to_xpos(move_str[0:1])
        yfrom = 8 - int(move_str[1:2]) # The board is drawn "upside down", so flip the y coordinate.
        xto = letter_to_xpos(move_str[2:3])
        yto = 8 - int(move_str[3:4]) # The board is drawn "upside down", so flip the y coordinate.
        return ai.Move(xfrom, yfrom, xto, yto, False), postBoard, postProcessedImage
    except ValueError:
        print("Invalid format. Example: A2 A4")
        return get_user_move(2), postBoard, postProcessedImage ## Willem Change: only prompt for move over text if invalid format

# Returns a valid move based on the users input.
def get_valid_user_move(board):
    attempt = 1
    while True:
        move, postBoard, postProcessedImage = get_user_move(attempt)
        attempt = 2
        valid = False
        possible_moves = board.get_possible_moves(pieces.Piece.WHITE)
        # No possible moves
        if (not possible_moves):
            return 0

        for possible_move in possible_moves:
            if (move.equals(possible_move)):
                move.castling_move = possible_move.castling_move
                valid = True
                break

        if (valid):
            break
        else:
            print("Invalid move.")
    return move, postBoard, postProcessedImage

# Converts a letter (A-H) to the x position on the chess board.
def letter_to_xpos(letter):
    letter = letter.upper()
    if letter == 'A':
        return 0
    if letter == 'B':
        return 1
    if letter == 'C':
        return 2
    if letter == 'D':
        return 3
    if letter == 'E':
        return 4
    if letter == 'F':
        return 5
    if letter == 'G':
        return 6
    if letter == 'H':
        return 7

    raise ValueError("Invalid letter.")

#
# Entry point.
#
if __name__ == "__main__":
    board = board.Board.new()
    print(board.to_string())

    ## Willem Change: Added chess.py Game object ##
    chessGame = chess.Game()

    while True:
        move, postBoard, postProcessedImage = get_valid_user_move(board)
        if (move == 0):
            if (board.is_check(pieces.Piece.WHITE)):
                print("Checkmate. Black Wins.")
                break
            else:
                print("Stalemate.")
                break

        board.perform_move(move)

        print("User move: " + move.to_string())
        print(board.to_string())

        ai_move = ai.AI.get_ai_move(board, [])
        if (ai_move == 0):
            if (board.is_check(pieces.Piece.BLACK)):
                print("Checkmate. White wins.")
                break
            else:
                print("Stalemate.")
                break
        chessGame.makeAIMove(ai_move, postBoard)
        board.perform_move(ai_move)
        print("AI move: " + ai_move.to_string())
        print(board.to_string())
