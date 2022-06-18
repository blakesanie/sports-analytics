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

print("todaysDate", todaysDate)
sched = pd.DataFrame(statsapi.schedule(date=todaysDate))

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

for game, pbp in gameData:
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
    print(filename)
    postTweetWithFilenames(message, [filename])
    print('waiting 2 minutes')
    time.sleep(60 * 2)

print("posted", len(gameData), "games")

with open("history.txt", "w") as f:
    f.write(
        todaysDate
        + "\n"
        + "\n".join((processedGames + list(notProcessed["game_id"].astype(str))))
    )
