from datetime import datetime
from pytz import timezone
import statsapi
import pandas as pd
from overTime import runsOverGame
from threading import Thread
import faulthandler; faulthandler.enable()
from game import getPlayByPlay
from twitter import postTweetWithFilenames


try:
    with open('./history.txt') as file:
        print('history file found')
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]
        storedDate = lines[0]
        processedGames = lines[1:]
except FileNotFoundError as e:
    print('history file NOT FOUND')
    storedDate = None
    processedGames = []

tz = timezone('Pacific/Honolulu')
todaysDate = datetime.now(tz).strftime('%Y-%m-%d')

if storedDate is not None and storedDate != todaysDate:
    print('it is a new day!')
    processedGames = []

print('todaysDate', todaysDate)
# todaysDate = '2022-05-30'
sched = pd.DataFrame(statsapi.schedule(date=todaysDate))

final = sched.loc[(sched['status'] == 'Final') | (sched['status'] == 'Game Over')]

notProcessed = final.loc[~final['game_id'].astype(str).isin(processedGames)]

def getGameData(game, gameData):
    pbp = getPlayByPlay(game['game_id'])
    gameData.append((game, pbp))
    # runsOverGame('', '', '', game=game, battingStats=['runs'], pitchingStats=['pitcherCount'], markerLine='runs', xLabel="Time (US/Eastern)", yLabel="Runs", title="Runs over Time", legendLocation='best')

threads = []

gameData = []

for game in notProcessed.to_dict(orient="records"):
    threads.append(Thread(target=getGameData, args=(game, gameData)))

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

for game, pbp in gameData:
    filename, message = runsOverGame('', '', '', game=game, pbp=pbp, battingStats=['runs'], pitchingStats=['pitcherCount'], markerLine='runs',
                 xLabel="Time (US/Eastern)", yLabel="Runs", title="Runs over Time", legendLocation='best')
    print(filename)
    postTweetWithFilenames(message, [filename])

print('posted', len(gameData), 'games')

with open('history.txt', 'w') as f:
    f.write(todaysDate + '\n' + '\n'.join((processedGames + list(notProcessed['game_id'].astype(str)))))