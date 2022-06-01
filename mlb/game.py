import statsapi
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import pickle


def getPlayByPlay(gameId):
    filename = f"./cache/{gameId}.pkl"
    try:
        file = open(filename, "rb")
        out = pickle.load(file)
        file.close()
        print(f'found cached play by play for game {gameId}')
        return out
    except:
        pass


    timeCodes = statsapi.get('game_timestamps', {'gamePk': gameId})

    homePitching = []
    awayPitching = []
    homeBatting = []
    awayBatting = []
    for timeCode in tqdm(timeCodes):
        data = statsapi.boxscore_data(gameId, timecode=timeCode)
        timeStamp = datetime.strptime(timeCode, '%Y%m%d_%H%M%S')
        timeStamp = timeStamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        homePitching.append({**data['home']['teamStats']['pitching'], **{
                            'pitcherCount': len(data['homePitchers']) - 1, 'timeStamp': timeStamp}})
        awayPitching.append({**data['away']['teamStats']['pitching'], **{
                            'pitcherCount': len(data['awayPitchers']) - 1, 'timeStamp': timeStamp}})
        homeBatting.append(
            {**data['home']['teamStats']['batting'], **{'timeStamp': timeStamp}})
        awayBatting.append(
            {**data['away']['teamStats']['batting'], **{'timeStamp': timeStamp}})

    homePitching = pd.DataFrame(homePitching).set_index('timeStamp')
    homePitching.index = pd.to_datetime(
        homePitching.index).tz_convert('US/Eastern')
    awayPitching = pd.DataFrame(awayPitching).set_index('timeStamp')
    awayPitching.index = pd.to_datetime(
        awayPitching.index).tz_convert('US/Eastern')
    homeBatting = pd.DataFrame(homeBatting).set_index('timeStamp')
    homeBatting.index = pd.to_datetime(
        homeBatting.index).tz_convert('US/Eastern')
    awayBatting = pd.DataFrame(awayBatting).set_index('timeStamp')
    awayBatting.index = pd.to_datetime(
        awayBatting.index).tz_convert('US/Eastern')

    out = [homePitching, awayPitching, homeBatting, awayBatting]
    filehandler = open(filename, "wb")
    pickle.dump(out, filehandler)
    filehandler.close()
    return out


def getGame(team1, team2, date, gameIndex=0):
    out = statsapi.schedule(
        date=date, team=team1, opponent=team2)[gameIndex]
    print('game', out)
    return out



def getScoringPlays(gameId):
    return statsapi.game_scoring_play_data(gameId)
