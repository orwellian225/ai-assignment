import random
import chess
import chess.engine
import reconchess as rc
import reconchess.utilities as rcu
import sys

stockfish_path = "/opt/homebrew/Cellar/stockfish/16.1/bin/stockfish"


class RandomSensing(rc.Player):
    def __init__(self):
        self.colour = False

        self.board = None
        self.my_board = None

        self.current_move = 0

        self.states = set()

    # ReconChess Player Requirements
    def handle_game_start(self, color: chess.Color, board: chess.Board, opponent_name: str):
        self.colour = color
        self.my_colour = "White" if color else "Black"
        self.opp_colour = "Black" if color else "White"

        self.board = board
        self.board.reset()
        self.board.turn = self.colour

        self.my_board = rcu.without_opponent_pieces(self.board)
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)

        self.states.add(self.board.board_fen())

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: int | None):
        self.current_move += 1
        print(f'\nMove {self.current_move}')
        print('--------------------------------')
        print(f'{self.my_colour} in {self.my_board.board_fen()}')
        print(f'{self.opp_colour} in {len(self.states)} possible states')

        removed_states = set()
        print(f'Opp move result: removed {len(removed_states)} | {len(removed_states) / len(self.states) * 100: .2f}%')

    def choose_sense(self, sense_actions: list[chess.Square], move_actions: list[chess.Move], seconds_left: float) -> chess.Square | None:
        # Remove the squares around the edges of the board (remove rank 1 & 8, remove file a & h)
        sense_actions = sense_actions[8:56]  # removing ranks 1 & 8
        reduced_sense_actions = []
        for r in range(6):  # remove files a & h
            start = r * 8 + 1
            end = start + 6
            reduced_sense_actions.extend(sense_actions[start:end])

        selected_sense_square = random.choice(reduced_sense_actions)
        print(f'Sense choice: {chess.square_name(selected_sense_square)}')
        return selected_sense_square

    def handle_sense_result(self, sense_result: rc.List[rc.Tuple[chess.Square | chess.Piece | None]]):
        removed_states = set()
        print(f'Sense result: removed {len(removed_states)} | {len(removed_states) / len(self.states) * 100: .2f}%')
        pass

    def choose_move(self, move_actions: list[chess.Move], seconds_left: float) -> chess.Move | None:
        removed_states = set()
        print(f'Random prune result: removed {len(removed_states)} | {len(removed_states) / len(self.states) * 100: .2f}%')

        return None

    def handle_move_result(self, requested_move: chess.Move | None, taken_move: chess.Move | None, captured_opponent_piece: chess.Color, capture_square: chess.Square | None):
        removed_states = set()
        print(f'My move result: removed {len(removed_states)} | {len(removed_states) / len(self.states) * 100: .2f}%')

    def handle_game_end(self, winner_color: chess.Color | None, win_reason: rc.WinReason | None, game_history: rc.GameHistory):
        try:
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            print("Failed to terminate engine", sys.stderr)
