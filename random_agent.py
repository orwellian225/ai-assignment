import random
import chess
import chess.engine
import reconchess as rc

class RandomAgent(rc.Player):
    def handle_game_start(self, color: chess.Color, board: chess.Board, opponent_name: str):
        pass

    def handle_opponent_move_result(self, captured_my_piece: chess.Color, capture_square: int | None):
        pass

    def choose_sense(self, sense_actions: list[chess.Square], move_actions: list[chess.Move], seconds_left: float) -> chess.Square | None:
        return random.choice(sense_actions)

    def choose_move(self, move_actions: list[chess.Move], seconds_left: float) -> chess.Move | None:
        return random.choice(move_actions + [None])
    
    def handle_sense_result(self, sense_result: rc.List[rc.Tuple[chess.Square | chess.Piece | None]]):
        pass

    def handle_move_result(self, requested_move: chess.Move | None, taken_move: chess.Move | None, captured_opponent_piece: chess.Color, capture_square: chess.Square | None):
        pass

    def handle_game_end(self, winner_color: chess.Color | None, win_reason: rc.WinReason | None, game_history: rc.GameHistory):
        pass