import pandas as pd
from datetime import datetime, timezone
from teams import getTeamCols
from game import getGame, getScoringPlays, getPlayByPlay
from plot import plotLines
import pytz
import re

def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return ' '.join([m.group(0) for m in matches])

def capitalize(string):
    sentence = ' '.join(camel_case_split(word) for word in string.split(' '))
    return ' '.join(word[0].title() + word[1:] for word in sentence.split(' '))

def getPitchingChanges(pitching):
    return pitching.loc[pitching['pitcherCount'].diff() != 0][1:]

def getInningTimeStamps(pitching):
    inningsPitched = pitching['inningsPitched'].astype(float)
    outChanges = pitching.loc[inningsPitched.diff() != 0]
    outChanges = outChanges[1:] # remove 0 outs at start of game
    inningsPitched = outChanges['inningsPitched'].astype(float)
    inningChanges = outChanges.loc[inningsPitched % 1 == 0]
    return outChanges, inningChanges


def runsOverGame(teamName1, teamName2, date, battingStats=[], pitchingStats=[], xLabel=None, yLabel=None, title=None, legendLocation='lower right'):

    cols = ['id', 'primary', 'name', 'display_code']
    teams = {
        'away': dict(zip(cols, getTeamCols(teamName1, columns=cols))),
        'home': dict(zip(cols, getTeamCols(teamName2, columns=cols)))
    }

    statsGame = getGame(teams['away']['id'], teams['home']['id'], date)

    startTime = pd.DataFrame([{'startTime': statsGame['game_datetime']}]).set_index('startTime')
    startTime.index = pd.to_datetime(
        startTime.index).tz_convert('US/Eastern')
    startTime = startTime.index[0]

    if statsGame['away_name'] != teams['away']['name']:
        temp = teams['away']
        teams['away'] = teams['home']
        teams['home'] = temp

    homePitching, awayPitching, homeBatting, awayBatting = getPlayByPlay(statsGame['game_id'])

    awayOutChanges, awayInningChanges = getInningTimeStamps(homePitching)
    homeOutChanges, homeInningChanges = getInningTimeStamps(awayPitching)

    allInnings = pd.concat((awayInningChanges, homeInningChanges))
    allInnings.loc[startTime] = 0
    allInnings = allInnings.sort_index()
    innings = allInnings[:-1]

    inningsTimestamps = allInnings.index.values
    top = True
    inningsMarkers = []
    for i in range(1, len(inningsTimestamps)):
        inningsMarkers.append((inningsTimestamps[i-1] + (inningsTimestamps[i] - inningsTimestamps[i-1]) / 2, f"{'T' if top else 'B'}{(i+1)//2}"))
        top = not top


    print('potential battingStats:', homeBatting.columns)
    print('potential pitchingStats:', homePitching.columns)

    dfs = []

    if 'runs' in battingStats:
        plays = getScoringPlays(statsGame['game_id'])
        points = [{
            'timeStamp': statsGame['game_datetime'],
            'home': 0,
            'away': 0
        }]
        points.extend([{
            'timeStamp': play['about']['endTime'],
            'home': play['result']['homeScore'],
            'away': play['result']['awayScore'],
            'home Label': f"{play['result']['description'].split(' ')[1]}" if play['about']['halfInning'] == 'bottom' else None,
            'away Label': f"{play['result']['description'].split(' ')[1]}" if play['about']['halfInning'] == 'top' else None,
        } for play in plays['plays']])

        points = pd.DataFrame(points)

        points = points.set_index('timeStamp')
        points.index = pd.to_datetime(
            points.index).tz_convert('US/Eastern')

        endOfGame = {
            'home': points['home'][-1],
            'away': points['away'][-1]
        }
        points.loc[homeBatting.index[-1]] = [endOfGame.get(col, None) for col in points.columns]

        awayPitchingChanges = getPitchingChanges(awayPitching)[['pitcherCount']].rename(columns={'pitcherCount': 'home pitchersFaced'})
        homePitchingChanges = getPitchingChanges(homePitching)[['pitcherCount']].rename(columns={'pitcherCount': 'away pitchersFaced'})

        points = pd.concat((points, awayPitchingChanges, homePitchingChanges))
        points = points.sort_index()
        points['home'] = points['home'].fillna(method='ffill')
        points['away'] = points['away'].fillna(method='ffill')

        dfs.append(points)

    if 'runs' in battingStats:
        battingStats.remove('runs')

    homeDf = pd.DataFrame()
    awayDf = pd.DataFrame()

    if len(battingStats) > 0:
        df = homeBatting[battingStats]
        renames = {col: f"home {col}" for col in df.columns}
        df = df.rename(columns=renames)
        homeDf = pd.concat((homeDf, df))

        df = awayBatting[battingStats]
        renames = {col: f"away {col}" for col in df.columns}
        df = df.rename(columns=renames)
        awayDf = pd.concat((awayDf, df))

    if len(pitchingStats) > 0:
        df = homePitching[pitchingStats]
        renames = {col: f"home {col}" for col in df.columns}
        df = df.rename(columns=renames)
        homeDf = pd.concat((homeDf, df))

        df = awayPitching[pitchingStats]
        renames = {col: f"away {col}" for col in df.columns}
        df = df.rename(columns=renames)
        awayDf = pd.concat((awayDf, df))

    homeDf = homeDf.sort_index().fillna(method="ffill")
    awayDf = awayDf.sort_index().fillna(method="ffill")

    if len(homeDf) > 0:
        dfs.append(homeDf)
    if len(awayDf) > 0:
        dfs.append(awayDf)

    cmap = {}
    cmap[teams['home']['display_code']] = teams['home']['primary']
    cmap[teams['away']['display_code']] = teams['away']['primary']

    for i, df in enumerate(dfs):
        renamings = {}
        for col in df.columns:
            newName = col.replace('homeRun', 'Home Run').replace('home', teams['home']['display_code']).replace(
                'away', teams['away']['display_code'])
            newName = capitalize(newName)
            if col != newName:
                renamings[col] = newName
        dfs[i] = df.rename(
            columns=renamings).loc[df.index >= startTime]

    if date[0] == '0':
        date = date[1:]

    return plotLines(dfs, xLabel='Time (US/Eastern)', yLabel='Runs', title=f"{teams['away']['display_code']} @ {teams['home']['display_code']}, {date}{f', {title}' if title else ''}", cmap=cmap, legendLocation=legendLocation, innings=innings, inningsMarkers=inningsMarkers)
