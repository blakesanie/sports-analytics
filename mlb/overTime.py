import pandas as pd
from datetime import datetime, timezone
from teams import getTeamColsByName
from game import getGame, getScoringPlays, getPlayByPlay
from plot import plotLines
import pytz
import re
from color import color_similarity

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


def runsOverGame(teamName1, teamName2, date, game=None, pbp=None, battingStats=[], pitchingStats=[], xLabel=None, yLabel=None, title=None, legendLocation='lower right', markerLine=None, homeColor=None, awayColor=None, twitterLocation=None, legendCoords=None):
    cols = ['id', 'primary', 'name', 'display_code']
    if game is None:
        teams = {
            'away': dict(zip(cols, getTeamColsByName(teamName1, columns=cols))),
            'home': dict(zip(cols, getTeamColsByName(teamName2, columns=cols)))
        }
        statsGame = getGame(teams['away']['id'], teams['home']['id'], date)
        if statsGame['away_name'] != teams['away']['name']:
            temp = teams['away']
            teams['away'] = teams['home']
            teams['home'] = temp
    else:
        teams = {
            'away': dict(zip(cols, getTeamColsByName(game['away_name'], type='full', columns=cols))),
            'home': dict(zip(cols, getTeamColsByName(game['home_name'], type='full', columns=cols)))
        }
        statsGame = game

    startTime = pd.DataFrame([{'startTime': statsGame['game_datetime']}]).set_index('startTime')
    startTime.index = pd.to_datetime(
        startTime.index).tz_convert('US/Eastern')
    startTime = startTime.index[0]


    homePitching, awayPitching, homeBatting, awayBatting = getPlayByPlay(statsGame['game_id']) if pbp is None else pbp

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


    homeDf = pd.DataFrame()
    awayDf = pd.DataFrame()

    if 'runs' in battingStats:
        plays = getScoringPlays(statsGame['game_id'])

        homePoints = [{
            'timeStamp': statsGame['game_datetime'],
            'home runs': 0
        }]

        awayPoints = [{
            'timeStamp': statsGame['game_datetime'],
            'away runs': 0
        }]

        for play in plays['plays']:
            if play['about']['halfInning'] == 'top':
                awayPoints.append({
                    'timeStamp': play['about']['endTime'],
                    'away runs': play['result']['awayScore'],
                    'away runs label': str(play['result']['description'].split(' ')[1])
                })
            else:
                homePoints.append({
                    'timeStamp': play['about']['endTime'],
                    'home runs': play['result']['homeScore'],
                    'home runs label': str(play['result']['description'].split(' ')[1])
                })

        homePoints = pd.DataFrame(homePoints)
        awayPoints = pd.DataFrame(awayPoints)

        homePoints = homePoints.set_index('timeStamp')
        homePoints.index = pd.to_datetime(
            homePoints.index).tz_convert('US/Eastern')

        awayPoints = awayPoints.set_index('timeStamp')
        awayPoints.index = pd.to_datetime(
            awayPoints.index).tz_convert('US/Eastern')

        homeDf = pd.concat((homeDf, homePoints))

        awayDf = pd.concat((awayDf, awayPoints))

    if 'runs' in battingStats:
        battingStats.remove('runs')

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
        if 'pitcherCount' in pitchingStats:
            homePitchingChanges = getPitchingChanges(awayPitching)[['pitcherCount']].rename(
                columns={'pitcherCount': 'home pitchers faced'})
            homeDf = pd.concat((homeDf, homePitchingChanges))

            awayPitchingChanges = getPitchingChanges(homePitching)[['pitcherCount']].rename(
                columns={'pitcherCount': 'away pitchers faced'})
            awayDf = pd.concat((awayDf, awayPitchingChanges))

            pitchingStats.remove('pitcherCount')


        df = homePitching[pitchingStats]
        renames = {col: f"home {col}" for col in df.columns}
        df = df.rename(columns=renames)
        homeDf = pd.concat((homeDf, df))

        df = awayPitching[pitchingStats]
        renames = {col: f"away {col}" for col in df.columns}
        df = df.rename(columns=renames)
        awayDf = pd.concat((awayDf, df))


    dfs = []

    if len(homeDf) > 0:
        dfs.append(homeDf)
    if len(awayDf) > 0:
        dfs.append(awayDf)

    cmap = {}
    cmap[teams['home']['display_code']] = teams['home']['primary'] if homeColor is None else homeColor
    cmap[teams['away']['display_code']] = teams['away']['primary'] if awayColor is None else awayColor

    similarity, lightest = color_similarity(*list(cmap.values()))

    amap={}

    if similarity < 150:
        for key, value in cmap.items():
            if value == lightest:
                amap[key] = 0.5 + similarity / 150 * 0.3
                break

    print(similarity, cmap)
    for i, df in enumerate(dfs):
        df = df.sort_index()
        df = df.loc[df.index >= startTime]
        if markerLine:
            cols = list(df.columns)
            prefix = cols[0].split(' ')[0]
            newOrder = [prefix + ' ' + markerLine]
            for col in cols:
                if col != newOrder[0]:
                    newOrder.append(col)
            df = df[newOrder]
        renamings = {}
        for col in df.columns:
            if not (col.endswith('label') or col.endswith('pitchers faced')):
                df[col] = df[col].fillna(method='ffill').fillna(0)
            newName = col.replace('homeRun', 'Home Run').replace('home', teams['home']['display_code']).replace(
                'away', teams['away']['display_code'])
            newName = capitalize(newName)
            if col != newName:
                renamings[col] = newName
        dfs[i] = df.rename(
            columns=renamings)

    gameDate = statsGame['game_date']
    year = int(gameDate[:4])
    month = int(gameDate[5:7])
    day = int(gameDate[-2:])

    filename = plotLines(dfs, xLabel=xLabel, yLabel=yLabel, title=f"{teams['away']['display_code']} @ {teams['home']['display_code']}, {month}/{day}/{year}{f', {title}' if title else ''}", cmap=cmap, amap=amap, legendLocation=legendLocation, innings=innings, inningsMarkers=inningsMarkers, legendCoords=legendCoords, twitterLocation=twitterLocation)
    message = statsGame['summmary']
    return filename, message