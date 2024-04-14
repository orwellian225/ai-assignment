import sys
import chess

def sub1_main():

    input_fen = ""
    if len(sys.argv) == 2:
        input_fen = sys.argv[1]
    else:
        input_fen = input()

    board = chess.Board(input_fen)
    print(board)

def sub2_main():

    if len(sys.argv) == 3:
        input_fen = sys.argv[1]
        input_move = sys.argv[2]
    else:
        input_fen = input()
        input_move = input()

    board = chess.Board(input_fen)
    move = chess.Move.from_uci(input_move)

    if move in board.legal_moves:
        board.push(move)

    print(board.fen())

submission_id = 2
match submission_id:
    case 1:
        sub1_main()
    case 2:
        sub2_main()
    case _:
        print("No specified submission - please select a submission number", file=sys.stderr)