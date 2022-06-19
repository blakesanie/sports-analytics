from datetime import datetime
from pytz import timezone
import statsapi
import pandas as pd
from overTime import runsOverGame
from threading import Thread
import faulthandler
import time

faulthandler.enable()
from game import getPlayByPlay
from twitter import postTweetWithFilenames


try:
    with open("./history.txt") as file:
        print("history file found")
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]
        storedDate = lines[0]
        processedGames = lines[1:]
except FileNotFoundError as e:
    print("history file NOT FOUND")
    storedDate = None
    processedGames = []

# game schedule should recycle very early in the morning, Eastern time
tz = timezone("Pacific/Honolulu")
todaysDate = datetime.now(tz).strftime("%Y-%m-%d")

if storedDate is not None and storedDate != todaysDate:
    print("it is a new day!")
    processedGames = []

# todaysDate = '2022-06-01'

print("todaysDate", todaysDate)
sched = pd.DataFrame(statsapi.schedule(date=todaysDate))

# sched = sched[2:4]

print("scheduled games")
print(sched)

final = sched.loc[(sched["status"] == "Final") | (sched["status"] == "Game Over")]

notProcessed = final.loc[~final["game_id"].astype(str).isin(processedGames)]


def getGameData(game, gameData):
    pbp = getPlayByPlay(game["game_id"])
    gameData.append((game, pbp))


threads = []

gameData = []

for game in notProcessed.to_dict(orient="records"):
    # download PBP data in parallel to maximize CPU usage during IO tasks
    threads.append(Thread(target=getGameData, args=(game, gameData)))

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

i = 0
for game, pbp in gameData:
    if i > 0:
        print("waiting 2 minutes between")
        time.sleep(60 * 2)
    i += 1

    print("working on", game)
    try:
        filename, message = runsOverGame(
            "",
            "",
            "",
            game=game,  # provide our collected game and PBP data
            pbp=pbp,
            battingStats=["runs"],
            pitchingStats=["pitcherCount"],
            markerLine="runs",
            xLabel="Time (US/Eastern)",
            yLabel="Runs",
            legendLocation="best",
        )
    except Exception as e:
        print("could not process game with exception", e)
        continue
    processedGames.append(str(game["game_id"]))
    postTweetWithFilenames(message, [filename])

print("posted", len(gameData), "games")

with open("history.txt", "w") as f:
    f.write(todaysDate + "\n" + "\n".join((processedGames)))
