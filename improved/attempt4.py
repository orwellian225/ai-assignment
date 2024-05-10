import random
import chess
import chess.engine
import reconchess as rc
import reconchess.utilities as rcu
import logging
import heapq
import numpy as np
import math as m
import sys

stockfish_path = "/opt/homebrew/Cellar/stockfish/16.1/bin/stockfish"

def select_best_states(states: set[str], turn: chess.Color, engine: chess.engine.SimpleEngine, state_limit: int) -> list[str]:
    """
        Not allowed to modify states variable
    """
    possible_states = list(states)
    if len(states) > state_limit:
        board = chess.Board()
        board.turn = turn

        state_evaluations = {}
        for state in states:
            state_evaluations[state] = engine.analyse(board, chess.engine.Limit(depth=5))["score"].pov(turn)

        return heapq.nlargest(state_limit, state_evaluations, key=lambda key: state_evaluations[key])
    else:
        return possible_states

def calculate_probabilites(states: set[str]) -> list[dict[chess.Piece, int]] | None:
    num_states = len(states)
    if num_states == 0:
        return None

    probabilites = [{}  for _ in chess.SQUARES]

    board = chess.Board()
    for state in states:
        board.set_board_fen(state)

        for square in chess.SQUARES:
            if probabilites[square] is None:
                probabilites[square] = {}

            current_piece = board.piece_at(square)
            if current_piece not in probabilites[square].keys():
                probabilites[square][current_piece] = 1 / num_states
            else:
                probabilites[square][current_piece] += 1 / num_states

    return probabilites

def calculate_entropy(probabilites: list[dict[chess.Piece, int]]) -> np.array:
    entropies = np.zeros(8 * 8)
    convolved_entropies = np.zeros(8 * 8)

    for square in chess.SQUARES:
        for pieces in probabilites[square].keys():
            entropies[square] -= probabilites[square][pieces] * m.log(probabilites[square][pieces], 2)

    kernel = [-9, -8, -7, -1, 0, 1, 7, 8, 9]
    for square in chess.SQUARES:
        for square_shift in kernel:
            if square + square_shift >= 0 and square + square_shift < 64:
                convolved_entropies[square] += entropies[square + square_shift]

    convolved_entropies = np.reshape(convolved_entropies, (8,8))

    return convolved_entropies


def generate_moves(board: chess.Board):
    moves = [chess.Move.null()]
    for m in board.generate_pseudo_legal_moves():
        moves.append(m)

    for m in rcu.without_opponent_pieces(board).generate_castling_moves():
        if not rcu.is_illegal_castle(board, m):
            moves.append(m)

    for m in rcu.pawn_capture_moves_on(board):
        moves.append(m)

    return moves


# Update all states by a move
def apply_move(states: set[str], move: chess.Move, turn: chess.Color):
    """
        IMPORTANT ASSUMPTION: The move supplied is an applicable move
        i.e. If a state says the move is invalid, then the state must be invalid
    """
    board = chess.Board()
    board.turn = turn

    next_states = set()

    num_removed = 0

    for state in states:
        board.set_board_fen(state)

        try:
            board.push(move)
            next_states.add(board.board_fen())
            board.pop()
        except AssertionError:
            # Attempted move invalid => state is invalid => remove state
            num_removed += 1

    return (next_states, num_removed)


# Update all states by all possible moves for that state
def evolve_states(states: set[str], turn: chess.Color, capture_square: chess.Square | None):
    board = chess.Board()
    board.turn = turn

    new_states = set()
    ignored_states = 0

    for state in states:
        board.set_board_fen(state)
        moves = generate_moves(board)

        for m in moves:
            if capture_square is not None and m.to_square == capture_square:
                board.push(m)
                new_states.add(board.board_fen())
                board.pop()
            elif capture_square is not None and m.to_square != capture_square:
                ignored_states += 1
            elif capture_square is None:
                board.push(m)
                new_states.add(board.board_fen())
                board.pop()

    return new_states, ignored_states

class OpeningFishyEntropy(rc.Player):
    def __init__(self):
        self.colour = False
        self.my_board = None
        self.current_move = 0
        self.states = set()
        self.logger = logging.getLogger('entropic.opening')
        logging.basicConfig(filename="improved-4.log", encoding="utf-8", level=logging.DEBUG)

        self.perform_opening = True
        self.opening_moves = {
            chess.WHITE: [chess.Move.from_uci("e2e3"), chess.Move.from_uci("f1c4"), chess.Move.from_uci("d1h5"), chess.Move.from_uci("c4f7")],
            chess.BLACK: [chess.Move.from_uci("e7e6"), chess.Move.from_uci("f8c5"), chess.Move.from_uci("d8h4"), chess.Move.from_uci("c5f2")]
        }

    # ReconChess Player Requirements
    def handle_game_start(self, color: chess.Color, board: chess.Board, opponent_name: str):
        self.colour = color
        self.my_colour = "White" if color else "Black"
        self.opp_colour = "Black" if color else "White"

        board.reset()
        board.turn = self.colour

        self.my_board = rcu.without_opponent_pieces(board)
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)

        self.sets = set()
        self.states.add(board.board_fen())

        self.current_move = 0

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: int | None):
        self.current_move += 1
        # print('--------------------------------')
        # print(f'Move {self.current_move}')
        # print(f'{self.my_colour} in {self.my_board.board_fen()}')
        # print(f'{self.opp_colour} in {len(self.states)} possible states')

        if self.colour == chess.WHITE and self.current_move == 1:
            return

        # Generate opponents possible moves
        self.states, num_removed_states = evolve_states(self.states, not self.colour, capture_square)

        # print(f'Opp move result:\tremoved {num_removed_states}')

    def choose_sense(self, sense_actions: list[chess.Square], move_actions: list[chess.Move], seconds_left: float) -> chess.Square | None:
        # print(f'{self.my_colour} time left:\t{seconds_left} seconds')

        probabilites = calculate_probabilites(self.states)
        entropy = calculate_entropy(probabilites) if probabilites is not None else np.zeros((8,8))

        # Remove the squares around the edges of the board (remove rank 1 & 8, remove file a & h)
        entropy = np.reshape(entropy[1:7, 1:7], (6*6)) # removing ranks 1 & 8

        sense_actions = np.reshape(np.reshape(np.array(sense_actions), (8,8))[1:7, 1:7], (6*6))
        max_indices = np.argwhere(entropy == np.amax(entropy))

        selected_sense_square = sense_actions[random.choice(max_indices)]

        # print(f'Sense choice:\t{chess.square_name(selected_sense_square)} with entropy {np.reshape(entropy, (6*6))[selected_indices]} | max entropy {np.max(entropy)}')
        return int(selected_sense_square)

    def handle_sense_result(self, sense_result: rc.List[rc.Tuple[chess.Square | chess.Piece | None]]):
        # before_state_size = len(self.states)
        removed_states = set()

        board = chess.Board()
        for state in self.states:
            board.set_board_fen(state)
            for sense_square in sense_result:
                if board.piece_at(sense_square[0]) != sense_square[1]:
                    removed_states.add(state)
                    break

        for removed_state in removed_states:
            self.states.remove(removed_state)

        # print(f'Sense result:\t\tremoved {len(removed_states)} of {before_state_size} | {len(removed_states) / before_state_size if before_state_size != 0 else 1e6 * 100:.2f}%')

    def choose_move(self, move_actions: list[chess.Move], seconds_left: float) -> chess.Move | None:
        board = chess.Board()
        for state in self.states:
            board.set_board_fen(state)
            board.clear_stack()
            board.turn = self.colour

            opposing_king_square = board.king(not self.colour)
            possible_moves = generate_moves(board)
            for move in possible_moves:
                if opposing_king_square == move.to_square and move in move_actions:
                    return move

        # If in the opening stages of the game, play a specific move sequence to try capture the opponents king
        if self.perform_opening:
            selected_move = self.opening_moves[self.colour][self.current_move - 1]

            if self.current_move >= len(self.opening_moves[self.colour]):
                self.perform_opening = False

            if selected_move in move_actions:
                return selected_move
            else:
                return None
        else:
            # pick opponents best states for a bit of the minimax action lmao
            search_states = select_best_states(self.states, not self.colour, self.engine, 10_000)

            # print(f'Stockfish search:\t{len(search_states)} states at {10 / len(search_states) if len(search_states) != 0 else 1e6} seconds per state')
            selected_moves = {}

            try:
                result = self.engine.play(board, chess.engine.Limit(time=10 / len(search_states) if len(search_states) != 0 else 1e6))

                move_uci = result.move.uci() if result.move is not None else '0000'
                if move_uci not in selected_moves.keys():
                    selected_moves[move_uci] = 1
                else:
                    selected_moves[move_uci] += 1

            except chess.engine.EngineTerminatedError:
                print(f"Engine died: state {state}")
            except chess.engine.EngineError:
                print(f'Engine bad state {state}')

            nonexisting_moves = 0
            if len(selected_moves) != 0:
                moves_uci = []
                for mv in selected_moves.keys():
                    if chess.Move.from_uci(mv) not in move_actions:
                        moves_uci.append(mv)
                        nonexisting_moves += 1

                for mv in moves_uci:
                    selected_moves.pop(mv)

                if len(selected_moves) == 0:
                    return None

                # print(f"Nonexistant moves:\t{nonexisting_moves}")
                return chess.Move.from_uci(max(selected_moves, key=lambda key: selected_moves[key]))
            else:
                return None

    def handle_move_result(self, requested_move: chess.Move | None, taken_move: chess.Move | None, captured_opponent_piece: chess.Color, capture_square: chess.Square | None):

        # print(f'Move choice:\t\t{requested_move.uci() if requested_move else "0000"}')
        # print(f'Move taken:\t\t{taken_move.uci() if taken_move else "0000"}')

        before_state_size = len(self.states)
        num_invalid_move_for_state_removed = 0
        num_invalid_move_taken_removed = 0

        if taken_move:
            self.my_board.turn = self.colour
            self.my_board.push(taken_move)
            self.states, num_invalid_move_for_state_removed = apply_move(self.states, taken_move, self.colour)
        else:
            # prune the states that thought the move was valid
            # board = chess.Board()

            # removed_states = set()

            # for state in self.states:
            #     board.set_board_fen(state)
            #     board.turn = self.colour
            #     moves = generate_moves(board)

            #     if requested_move in moves:
            #         removed_states.add(state)
            #         num_invalid_move_taken_removed += 1

            # for removed_state in removed_states:
            #     try:
            #         self.states.remove(removed_state)
            #     except KeyError:
            #         print(f"Trying to remove non-existant state {removed_state}")

            # Because errors need to revisit this

            pass

        # print(f'My move result:\t\tremoved {num_invalid_move_for_state_removed + num_invalid_move_taken_removed} of {before_state_size} | {(num_invalid_move_for_state_removed + num_invalid_move_taken_removed) / before_state_size if before_state_size != 0 else 1e6 * 100:.2f}%')


    def handle_game_end(self, winner_color: chess.Color | None, win_reason: rc.WinReason | None, game_history: rc.GameHistory):
        try:
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            self.logger.error("Failed to terminate engine")
