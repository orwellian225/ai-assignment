import sys
import chess

from reconchess.utilities import without_opponent_pieces, is_illegal_castle

def moves(board):
    moves = ['0000']
    legal_moves = board.pseudo_legal_moves
    for i in legal_moves:
        moves.append(i.uci())
    for move in without_opponent_pieces(board).generate_castling_moves():
        moves.append(move.uci())
    moves.sort()
    return moves

def sub1_main():
    input_fen = ""
    if len(sys.argv) == 2:
        input_fen = sys.argv[1]
    else:
        input_fen = input()

    board = chess.Board(input_fen)
    move = moves(board)
    for i in move:
        print(i)
    
     
 
def sub2_main():
    input_fen = ""
    if len(sys.argv) == 2:
        input_fen = sys.argv[1]
    else:
        input_fen = input()

    board = chess.Board(input_fen)
    new_moves = moves(board)
    new_states = []
    for move in new_moves:
        move = chess.Move.from_uci(move)
        board.push(move)
        new_states.append(board.fen())
        board.pop()
    
    new_states.sort()
    for state in new_states:
        print(state)
    #pass

def sub3_main():
    input_fen = ""
    input_move = ""
    if len(sys.argv) == 3:
        input_fen = sys.argv[1]
        input_move = sys.argv[2]
    else:
        input_fen = input()
        input_move = input()

    board = chess.Board(input_fen)

    next_states = []
    for move in board.legal_moves:
        if move.uci()[2:4] == input_move:
            board.push(move)
            next_states.append(board.fen())
            board.pop()

    next_states.sort()
    for state in next_states:
        print(state)


def valid_state_from_sense(state_fen: str, sense: str):
    board = chess.Board(state_fen)
    sense_squares = sense.split(";")

    for square in sense_squares:
        square_components = square.split(":")
        square_id = square_components[0]
        square_piece = square_components[1]
        print(square, board.piece_at(square_id))
        if board.piece_at(square_id).symbol != square_piece:
            return False

    return True

def sub4_main():
    input_num_states = 0
    input_states = []
    input_sense = ""

    if len(sys.argv) == 4:
        input_num_states = int(sys.argv[1])
        input_states = sys.argv[2].split("\n")
        input_sense = sys.argv[3]
    else:
        input_num_states = int(input())
        for _ in range(input_num_states):
            input_states.append(input())
        input_sense = input() 

    for state_fen in input_states:
        if valid_state_from_sense(state_fen, input_sense):
            print(state_fen)


submission_id = 1
match submission_id:
    case 1:
        sub1_main()
    case 2:
        sub2_main()
    case 3:
        sub3_main()
    case 4:
        sub4_main()
    case _:
        print("No specified submission - please select a submission number", file=sys.stderr)