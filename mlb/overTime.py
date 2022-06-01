import pandas as pd
from datetime import datetime, timezone
from teams import getTeamColsByName, getTwitterInfoByFullName
from game import getGame, getScoringPlays, getPlayByPlay
from plot import plotLines
import pytz
import re
from color import color_similarity
import math
import random


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
    outChanges['inningsPitched'] = outChanges['inningsPitched'].astype(float)
    # in the case of a walk off, check if the last row is not a whole number
    isWalkOff = False
    if inningsPitched[-1] % 1 != 0 and inningsPitched[-1] > 8:
        lastRow = pitching.iloc[-1]
        lastRow['inningsPitched'] = math.ceil(float(lastRow['inningsPitched']))
        outChanges = outChanges.append(lastRow)
        isWalkOff = True
    inningsPitched = outChanges['inningsPitched']
    inningChanges = outChanges.loc[inningsPitched % 1 == 0]
    return outChanges, inningChanges, isWalkOff


def runsOverGame(teamName1, teamName2, date, game=None, pbp=None, gameIndex=0, battingStats=[], pitchingStats=[], xLabel=None, yLabel=None, title=None, legendLocation='lower right', markerLine=None, homeColor=None, awayColor=None, twitterLocation=None, legendCoords=None):
    cols = ['id', 'primary', 'name', 'display_code', 'teamName']
    if game is None:
        teams = {
            'away': dict(zip(cols, getTeamColsByName(teamName1, columns=cols))),
            'home': dict(zip(cols, getTeamColsByName(teamName2, columns=cols)))
        }
        statsGame = getGame(teams['away']['id'], teams['home']['id'], date, gameIndex=gameIndex)
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

    awayOutChanges, awayInningChanges, _ = getInningTimeStamps(homePitching)
    homeOutChanges, homeInningChanges, isWalkOff = getInningTimeStamps(awayPitching)


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
            capitalizedWordsEncountered = 0
            for word in play['result']['description'].replace(teams['home']['teamName'], '').replace(teams['away']['teamName'], '').split(' '):
                if len(word) > 0 and word[0].isalpha() and word[0] == word[0].upper():
                    if capitalizedWordsEncountered == 1:
                        regex = re.compile('[^a-zA-Z]')
                        lastName = regex.sub('', word)
                        break
                    capitalizedWordsEncountered += 1
            if play['about']['halfInning'] == 'top':
                awayPoints.append({
                    'timeStamp': play['about']['endTime'],
                    'away runs': play['result']['awayScore'],
                    'away runs label': lastName
                })
            else:
                homePoints.append({
                    'timeStamp': play['about']['endTime'],
                    'home runs': play['result']['homeScore'],
                    'home runs label': lastName
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

    walkOff = (homeDf.index[homeDf['home runs'].argmax()], homeDf['home runs'].max()) if isWalkOff else None

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

    doubleHeader = '' if statsGame['doubleheader'] == 'N' else f", Game {statsGame['game_num']} of 2"

    filename = plotLines(dfs, xLabel=xLabel, yLabel=yLabel, title=f"{teams['away']['display_code']} @ {teams['home']['display_code']}{doubleHeader}, {month}/{day}/{year}{f', {title}' if title else ''}", cmap=cmap, amap=amap, legendLocation=legendLocation, innings=innings, inningsMarkers=inningsMarkers, legendCoords=legendCoords, twitterLocation=twitterLocation, bang=walkOff)

    winningHandle, winningHashTags = getTwitterInfoByFullName(statsGame['winning_team'])
    losingHandle, losingHashTags = getTwitterInfoByFullName(statsGame['losing_team'])

    winningScore = max(statsGame['away_score'], statsGame['home_score'])
    losingScore = min(statsGame['away_score'], statsGame['home_score'])

    if isWalkOff:
        starter = 'Walk off! 💥'
    else:
        starter = random.choice(["Just now:", "Final:", "This just in:", "Moments ago:", "Final score:"])

    message = f"{starter} {winningHandle} ({winningScore}) > {losingHandle} ({losingScore}){doubleHeader}, {month}/{day}/{year} | {statsGame['venue_name']} {winningHashTags} {losingHashTags}"

    return filename, message