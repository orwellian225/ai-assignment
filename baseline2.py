import random
import chess
import chess.engine
import reconchess as rc
import reconchess.utilities as rcu
import logging
import sys

stockfish_path = "/opt/homebrew/Cellar/stockfish/16.1/bin/stockfish"

logger = logging.getLogger('sensing.random')
logging.basicConfig(filename="baseline.log", encoding="utf-8", level=logging.DEBUG)

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


def test():
    """
        USE this function to test all auxillary methods
    """

    if len(sys.argv) == 3:
        fen = str(sys.argv[1])
        turn = bool(int(sys.argv[2]))
    else:
        fen = str(input("Test fen string:"))
        turn = bool(int(input("Turn (0 - black, 1 - white)")))

    states = set()
    states.add(fen)
    states = sorted(evolve_states(states, turn))

    for state in states:
        print(state)


if __name__ == "__main__":
    test()


class RandomSensing(rc.Player):
    def __init__(self):
        self.colour = False
        self.my_board = None
        self.current_move = 0
        self.states = set()

    # ReconChess Player Requirements
    def handle_game_start(self, color: chess.Color, board: chess.Board, opponent_name: str):
        self.colour = color
        self.my_colour = "White" if color else "Black"
        self.opp_colour = "Black" if color else "White"

        board.reset()
        board.turn = self.colour

        self.my_board = rcu.without_opponent_pieces(board)
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)

        self.states.add(board.board_fen())

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: int | None):
        self.current_move += 1
        logger.debug(f'\nMove {self.current_move}')
        logger.debug('--------------------------------')
        logger.debug(f'{self.my_colour} in {self.my_board.board_fen()}')
        logger.debug(f'{self.opp_colour} in {len(self.states)} possible states')

        if self.colour == chess.WHITE and self.current_move == 1:
            return

        # Generate opponents possible moves
        self.states, num_removed_states = evolve_states(self.states, not self.colour, capture_square)

        logger.debug(f'Opp move result:\tremoved {num_removed_states}')

    def choose_sense(self, sense_actions: list[chess.Square], move_actions: list[chess.Move], seconds_left: float) -> chess.Square | None:
        logger.debug(f'{self.my_colour} time left:\t{seconds_left} seconds')

        # Remove the squares around the edges of the board (remove rank 1 & 8, remove file a & h)
        sense_actions = sense_actions[8:56]  # removing ranks 1 & 8
        reduced_sense_actions = []
        for r in range(6):  # remove files a & h
            start = r * 8 + 1
            end = start + 6
            reduced_sense_actions.extend(sense_actions[start:end])

        selected_sense_square = random.choice(reduced_sense_actions)
        logger.debug(f'Sense choice:\t\t{chess.square_name(selected_sense_square)}')
        return selected_sense_square

    def handle_sense_result(self, sense_result: rc.List[rc.Tuple[chess.Square | chess.Piece | None]]):
        before_state_size = len(self.states)
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

        logger.debug(f'Sense result:\t\tremoved {len(removed_states)} of {before_state_size} | {len(removed_states) / before_state_size if before_state_size != 0 else 1e6 * 100:.2f}%')

    def choose_move(self, move_actions: list[chess.Move], seconds_left: float) -> chess.Move | None:
        before_state_size = len(self.states)
        removed_states = set()

        if len(self.states) > 10_000:
            removed_states = random.sample(list(self.states), len(self.states) - 10_000)

        for removed_state in removed_states:
            self.states.remove(removed_state)

        logger.debug(f'Random prune result:\tremoved {len(removed_states)} of {before_state_size} | {len(removed_states) / before_state_size if before_state_size != 0 else 1e6 * 100:.2f}%')

        invalid_states = 0

        logger.debug(f'Stockfish search:\t{len(self.states)} states at {10 / len(self.states) if len(self.states) != 0 else 1e6} seconds per state')
        board = chess.Board()
        selected_moves = {}
        for state in self.states:
            board.set_board_fen(state)
            board.clear_stack()
            board.turn = self.colour

            opposing_king_square = board.king(not self.colour)
            possible_moves = generate_moves(board)
            for move in possible_moves:
                if opposing_king_square == move.to_square and move in move_actions:
                    return move

            try:
                result = self.engine.play(board, chess.engine.Limit(time=10 / len(self.states) if len(self.states) != 0 else 1e6))

                move_uci = result.move.uci() if result.move != None else '0000'
                if move_uci not in selected_moves.keys():
                    selected_moves[move_uci] = 1
                else:
                    selected_moves[move_uci] += 1

            except chess.engine.EngineTerminatedError:
                logger.warning(f"Engine died: state {state}")
            except chess.engine.EngineError:
                logger.warning(f'Engine bad state {state}')

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

            logger.debug(f"Nonexistant moves:\t{nonexisting_moves}")
            return chess.Move.from_uci(max(selected_moves, key=lambda key: selected_moves[key]))
        else:
            return None

    def handle_move_result(self, requested_move: chess.Move | None, taken_move: chess.Move | None, captured_opponent_piece: chess.Color, capture_square: chess.Square | None):

        logger.debug(f'Move choice:\t\t{requested_move.uci() if requested_move else "0000"}')
        logger.debug(f'Move taken:\t\t{taken_move.uci() if taken_move else "0000"}')

        before_state_size = len(self.states)
        num_invalid_move_for_state_removed = 0
        num_invalid_move_taken_removed = 0

        if taken_move:
            self.my_board.turn = self.colour
            self.my_board.push(taken_move)
            self.states, num_invalid_move_for_state_removed = apply_move(self.states, taken_move, self.colour)
        else:
            # prune the states that thought the move was valid
            board = chess.Board()

            removed_states = set()

            for state in self.states:
                board.set_board_fen(state)
                board.turn = self.colour
                moves = generate_moves(board)

                if requested_move in moves:
                    removed_states.add(state)
                    num_invalid_move_taken_removed += 1

            for removed_state in removed_states:
                try:
                    self.states.remove(removed_state)
                except KeyError:
                    logger.warning(f"Trying to remove non-existant state {removed_state}")

        logger.debug(f'My move result:\t\tremoved {num_invalid_move_for_state_removed + num_invalid_move_taken_removed} of {before_state_size} | {(num_invalid_move_for_state_removed + num_invalid_move_taken_removed) / before_state_size if before_state_size != 0 else 1e6 * 100:.2f}%')


    def handle_game_end(self, winner_color: chess.Color | None, win_reason: rc.WinReason | None, game_history: rc.GameHistory):
        try:
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            logger.error("Failed to terminate engine")
