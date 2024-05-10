import reconchess as rc
from reconchess.bots.random_bot import RandomBot
from reconchess.bots.trout_bot import TroutBot
from baseline2 import RandomSensing
# from improved import EntropicSense
# from improved2 import NonPrunedEntropic
# from improved3 import FishyEntropy
from improved.attempt4 import OpeningFishyEntropy

import sys

if len(sys.argv) == 3:
    num_rounds = int(sys.argv[1])
    game_length = float(sys.argv[2])
else:
    num_rounds = int(input("Number of rounds: "))
    game_length = float(input("Seconds per game: "))

players = [TroutBot, OpeningFishyEntropy]

# game_rotations = [
#     [(0, 1), (2, 3)],
#     [(0, 2), (1, 3)],
#     [(0, 3), (1, 2)],

#     # Swap Colours
#     [(1, 0), (3, 2)],
#     [(2, 0), (3, 1)],
#     [(3, 0), (2, 1)],
# ]
game_rotations = [[(0, 1)], [(1, 0)]]

game_results = {}
for player in players:
    game_results[player] = {
        "draw": 0, "win": 0, "loss": 0
    }

for i in range(num_rounds):
    game_idx = i % len(game_rotations)
    game_rotation = game_rotations[game_idx]

    print(f"Game\t{'White': <16}\t{'Black': <16}\t{'Result': <8}\tReason")
    print(f"{'-':-<90}")
    for game in game_rotation:
        subgame = game_rotation.index(game)
        print(f"{i + 1}.{subgame + 1}\t{players[game[0]].__qualname__: <16}\t{players[game[1]].__qualname__: <16}", end="\n", flush=True)

        try:
            game_result, win_reason, _ = rc.play_local_game(players[game[0]](), players[game[1]](), seconds_per_player=game_length)
            if game_result is None:
                game_result_str = "Draw"
                game_results[players[game[0]]]["draw"] += 1
                game_results[players[game[1]]]["draw"] += 1
            elif game_result:
                game_result_str = "White"
                game_results[players[game[0]]]["win"] += 1
                game_results[players[game[1]]]["loss"] += 1
            else:
                game_result_str = "Black"
                game_results[players[game[0]]]["loss"] += 1
                game_results[players[game[1]]]["win"] += 1

            print(f"\t{game_result_str: <8}\t{win_reason}")
        except:
            print("(Error - Failed)")

    print(f"{'-':-<90}")

print(f"{'-':-<64}")
print(f"{'Agent Results': <20}|\tScore\tWins\tLosses\tDraws\tWin %")
print(f"{'-':-<20}|{'-':-<43}")
for agent in players:
    score = game_results[agent]['win'] * 1 + game_results[agent]['draw'] * 0.5
    print(f"{agent.__qualname__: <20}|\t{score}\t{game_results[agent]['win']}\t{game_results[agent]['loss']}\t{game_results[agent]['draw']}\t{game_results[agent]['win'] / num_rounds * 100:.2f}")
print(f"{'-':-<64}")
