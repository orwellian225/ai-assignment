import reconchess as rc
from reconchess.bots.random_bot import RandomBot
from reconchess.bots.trout_bot import TroutBot
from baseline2 import RandomSensing

import sys

if len(sys.argv) == 3:
    num_games_per_bot = int(sys.argv[1])
    game_length = float(sys.argv[2])
else:
    num_games_per_bot = int(input("Number of games"))
    game_length = float(input("Seconds per game"))

results = {
        "random": {"draw": 0, "win": 0, "loss": 0},
        "trout": {"draw": 0, "win": 0, "loss": 0}
}

for i in range(0, num_games_per_bot):

    if i % 2 == 0:
        winner_rand, _, _ = rc.play_local_game(RandomBot(), RandomSensing(), seconds_per_player=game_length)

        if winner_rand is None:
            results["random"]["draw"] += 1
        elif winner_rand:
            results["random"]["loss"] += 1
        else:
            results["random"]["win"] += 1

        winner_trout, _, _ = rc.play_local_game(TroutBot(), RandomSensing(), seconds_per_player=game_length)

        if winner_trout is None:
            results["trout"]["draw"] += 1
        elif winner_trout:
            results["trout"]["loss"] += 1
        else:
            results["trout"]["win"] += 1

    else:
        winner_rand, _, _ = rc.play_local_game(RandomSensing(), RandomBot(), seconds_per_player=game_length)

        if winner_rand is None:
            results["random"]["draw"] += 1
        elif winner_rand:
            results["random"]["win"] += 1
        else:
            results["random"]["loss"] += 1

        winner_trout, _, _ = rc.play_local_game(RandomSensing(), TroutBot(), seconds_per_player=game_length)

        if winner_trout is None:
            results["trout"]["draw"] += 1
        elif winner_trout:
            results["trout"]["win"] += 1
        else:
            results["trout"]["loss"] += 1

print("\n")
print("Vs Bot\tWins\tLosses\tDraws")
print(f"Random\t{results['random']['win']}\t{results['random']['loss']}\t{results['random']['draw']}")
print(f"Trout\t{results['trout']['win']}\t{results['trout']['loss']}\t{results['trout']['draw']}")
