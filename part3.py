import sys
import chess
import reconchess.utilities
import chess.engine

def moves(board):
    moves = [chess.Move.from_uci('0000')]
    legal_moves = board.pseudo_legal_moves
    for i in legal_moves:
        moves.append(i)
    for move in reconchess.utilities.without_opponent_pieces(board).generate_castling_moves():
        if not reconchess.utilities.is_illegal_castle(board,move) and move not in legal_moves:
            moves.append(move)
    return moves

# for automarker:
engine = chess.engine.SimpleEngine.popen_uci('/opt/stockfish/stockfish', setpgrp=True)
# engine = chess.engine.SimpleEngine.popen_uci('./stockfish/stockfish', setpgrp = True) #change for automarker: /opt/stockfish/stockfish

def sub1_main():
    input_fen = ""
    if len(sys.argv) == 2:
        input_fen = sys.argv[1]
    else:
        input_fen = input()

    board = chess.Board(input_fen)
    current_player = board.turn
    opposing_king_square = board.king(not current_player)

    possible_moves = moves(board)
    for move in possible_moves:
        attacked_square = move.to_square
        if opposing_king_square == attacked_square:
            selected_move = move
            break

    try:
        selected_move = engine.play(board, chess.engine.Limit(0.2)).move
    except chess.engine.EngineTerminatedError:
        print('Stockfish engine died')
    except chess.engine.EngineError:
        print('Stockfish engine bad state at {}'.format(board.fen()))

    print(selected_move.uci())

def sub2_main():
    input_num_states = 0
    input_states = []

    if len(sys.argv) >= 2:
        input_num_states = int(sys.argv[1])
        for i in range(input_num_states):
            input_states.append(sys.argv[2 + i])
    else:
        input_num_states = int(input())
        for _ in range(input_num_states):
            input_states.append(input())

    selected_moves = {}
    for state_fen in input_states:
        board = chess.Board(state_fen)
        current_player = board.turn
        opposing_king_square = board.king(not current_player)

        possible_moves = moves(board)
        for move in possible_moves:
            attacked_square = move.to_square
            if opposing_king_square == attacked_square:
                selected_move = move
                break

        try:
            selected_move = engine.play(board, chess.engine.Limit(0.2)).move
        except chess.engine.EngineTerminatedError:
            print('Stockfish engine died')
        except chess.engine.EngineError:
            print('Stockfish engine bad state at {}'.format(board.fen()))

        if selected_move.uci() not in selected_moves.keys():
            selected_moves[selected_move.uci()] = 1
        else:
            selected_moves[selected_move.uci()] += 1


    selected_moves = dict(sorted(selected_moves.items()))
    max_move = list(selected_moves.keys())[0]
    for move in selected_moves.keys():
        if selected_moves[move] > selected_moves[max_move]:
            max_move = move

    print(max_move)

submission_id = 2
match submission_id:
    case 1:
        sub1_main()
    case 2:
        sub2_main()
    case _:
        print("No specified submission - please select a submission number", file=sys.stderr)

engine.quit()