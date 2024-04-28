import random
import chess
import chess.engine
import reconchess as rc
import reconchess.utilities as rcu
import sys

# stockfish_path = "./stockfish/stockfish"
stockfish_path = "/opt/homebrew/Cellar/stockfish/16.1/bin/stockfish"
# stockfish_path = '/opt/stockfish/stockfish'

class RandomSensing(rc.Player):
    def __init__(self):
        self.colour = False
        self.opponent_name = "<null>"
        self.board = None
        self.current_move = 0

        self.states = set(())

    # Aux Methods
    def generate_possible_moves(self, state: str, turn: chess.Color) -> list[chess.Move]:
        self.board.set_board_fen(state)
        self.board.turn = turn
        possible_moves = set(())
        possible_moves.add(chess.Move.null())

        legal_moves = self.board.generate_pseudo_legal_moves()

        for legal_move in legal_moves:
            possible_moves.add(legal_move)

        for pawn_attack_move in rcu.pawn_capture_moves_on(self.board):
            possible_moves.add(pawn_attack_move)

        for possible_castle in self.board.generate_castling_moves():
            if not rcu.is_illegal_castle(self.board, possible_castle):
                possible_moves.append(possible_castle)

        return possible_moves

    def apply_moves(self, states: set[str], turn: chess.Color) -> set[str]:
        result = set(())
        self.board.turn = turn
        for state in states:
            self.board.set_board_fen(state)
            possible_moves = self.generate_possible_moves(state, turn)
            for move in possible_moves:
                self.board.push(move)
                result.add(self.board.board_fen())
                self.board.pop()

        return result

    def apply_move(self, states: set[str], move: chess.Move, turn: chess.Color) -> set[str]:
        result = set(())

        self.board.turn = turn
        for state in states:
            self.board.set_board_fen(state)
            self.board.push(move)
            result.add(self.board.board_fen())
            self.board.pop()

        return result

    ## ReconChess Player Requirements
    def handle_game_start(self, color: chess.Color, board: chess.Board, opponent_name: str):
        self.colour = color
        self.board = board
        self.opponent_name = opponent_name
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)

        self.board.reset()

        self.board.turn = self.colour
        self.my_board = rcu.without_opponent_pieces(self.board)
        self.states.add(self.board.board_fen())

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: int | None):
        print(f"\nMove: {self.current_move}")

        if self.colour == chess.WHITE and self.current_move == 0:
            return


        remove_states = set(())
        if captured_my_piece:
            # Remove any states that don't have my piece at the capture square
            for state in self.states:
                self.board.set_board_fen(state)
                if self.board.piece_at(capture_square).color == None:
                    remove_states.add(state)
        else:
            # If no capture, remove any states that have a capture
            for state in self.states:
                self.board.set_board_fen(state)
                self.board.turn = self.colour
                if rcu.without_opponent_pieces(self.board).board_fen() != self.my_board.board_fen():
                    remove_states.add(state)

        print(f'Opponent Capture {captured_my_piece}: remove {len(remove_states)} of {len(self.states)} states')
        for remove_state in remove_states:
            self.states.remove(remove_state)

    def choose_sense(self, sense_actions: list[chess.Square], move_actions: list[chess.Move], seconds_left: float) -> chess.Square | None:

        # Remove the squares around the edges of the board (remove rank 1 & 8, remove file a & h)
        sense_actions = sense_actions[8:56] # removing ranks 1 & 8
        reduced_sense_actions = []
        for r in range(6): # remove files a & h
            start = r * 8 + 1
            end = start + 6
            reduced_sense_actions.extend(sense_actions[start:end])

        return random.choice(reduced_sense_actions)

    def handle_sense_result(self, sense_result: rc.List[rc.Tuple[chess.Square | chess.Piece | None]]):
        remove_states = set(())
        for state in self.states:
            self.board.set_fen(state)
            for sense_square in sense_result:
                if self.board.piece_at(sense_square[0]) != sense_square[1]:
                    remove_states.add(state)
                    break

        print(f'Sense: remove {len(remove_states)} of {len(self.states)} states')
        for remove_state in remove_states:
            self.states.remove(remove_state)

    def choose_move(self, move_actions: list[chess.Move], seconds_left: float) -> chess.Move | None:
        print(f"{'White' if self.colour else 'Black'} pieces: {self.my_board.board_fen()}")
        print(f"{'White' if self.colour else 'Black'} time:", seconds_left, "s")
        print(f"{'White' if self.colour else 'Black'} possible {'white' if not self.colour else 'black'} states:", len(self.states))

        stockfish_moves = {}

        if len(self.states) > 10_000:
            num_removed_states = len(self.states) - 10_000
            print(f'Too many states: remove {num_removed_states} of {len(self.states)} states')
            removed_states = random.sample(sorted(self.states), num_removed_states)
            for removed_state in removed_states:
                self.states.remove(removed_state)

        for state in self.states:
            self.board.set_board_fen(state)
            self.board.turn = self.colour
            opposing_king_square = self.board.king(not self.colour)

            possible_moves = self.generate_possible_moves(state, self.colour)
            can_attack_king = False
            for move in possible_moves:
                attacked_square = move.to_square
                if opposing_king_square == attacked_square:
                    stockfish_move = move
                    can_attack_king = True
                    break

            try:
                if not can_attack_king and self.board.is_valid():
                    stockfish_move = self.engine.play(self.board, chess.engine.Limit(10 / len(self.states))).move
                elif not can_attack_king and not self.board.is_valid():
                    stockfish_move = chess.Move.null()
            except chess.engine.EngineTerminatedError:
                stockfish_move = chess.Move.null()
                print('Stockfish engine died with state {}'.format(self.board.fen()))
                self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)
            except chess.engine.EngineError:
                stockfish_move = chess.Move.null()
                print('Stockfish engine bad state at {}'.format(self.board.fen()))
                self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)

            if stockfish_move.uci() not in stockfish_moves.keys():
                stockfish_moves[stockfish_move.uci()] = 1
            else:
                stockfish_moves[stockfish_move.uci()] += 1

        stockfish_moves = dict(sorted(stockfish_moves.items()))
        if len(stockfish_moves) != 0:
            selected_move = list(stockfish_moves.keys())[0]
            for move in stockfish_moves.keys():
                if stockfish_moves[move] > stockfish_moves[selected_move]:
                    selected_move = move
        else:
            selected_move = chess.Move.null()

        return chess.Move.from_uci(selected_move) if selected_move != '0000' else None
    

    def handle_move_result(self, requested_move: chess.Move | None, taken_move: chess.Move | None, captured_opponent_piece: chess.Color, capture_square: chess.Square | None):
        self.current_move += 1

        self.my_board.turn = self.colour
        if taken_move:
            remove_states = set(())
            if captured_opponent_piece:
                # Remove any possible states that don't have an opponent piece at the capture square because a capture did take place
                for state in self.states:
                    self.board.set_board_fen(state)
                    if self.board.piece_at(capture_square) == None:
                        remove_states.add(state)

            print(f'Me Capture {captured_opponent_piece}: remove {len(remove_states)} of {len(self.states)} states')
            for remove_state in remove_states:
                self.states.remove(remove_state)

            self.my_board.push(taken_move)
            self.states = self.apply_move(self.states, taken_move, self.colour)
        else:
            # Played an invalid move
            # remove any state that causeed the invalid move

            # don't update the boards
            pass

        # Evolve the states by any possible moves
        self.states = self.apply_moves(self.states, not self.colour)

    def handle_game_end(self, winner_color: chess.Color | None, win_reason: rc.WinReason | None, game_history: rc.GameHistory):
        try:
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            print("Failed to terminate engine", sys.stderr)
