import pandas as pd
from datetime import datetime
from teams import getTeamCols
from game import getGame, getScoringPlays
from plot import plotLines


def runsOverGame(teamName1, teamName2, date):

    cols = ['id', 'primary', 'name', 'display_code']
    teams = {
        'away': dict(zip(cols, getTeamCols(teamName1, columns=cols))),
        'home': dict(zip(cols, getTeamCols(teamName2, columns=cols)))
    }

    statsGame = getGame(teams['away']['id'], teams['home']['id'], date)

    plays = getScoringPlays(statsGame['game_id'])
    points = [{
        'timeStamp': statsGame['game_datetime'],
        'homeScore': 0,
        'awayScore': 0
    }]
    points.extend([{
        'timeStamp': play['about']['endTime'],
        'homeScore': play['result']['homeScore'],
        'awayScore': play['result']['awayScore'],
        'homeScoreLabel': f"B{play['about']['inning']}, {play['result']['description'].split(' ')[1]}" if play['about']['halfInning'] == 'bottom' else None,
        'awayScoreLabel': f"T{play['about']['inning']}, {play['result']['description'].split(' ')[1]}" if play['about']['halfInning'] == 'top' else None,
    } for play in plays['plays']])

    # timeRange = points[-1]['timeStamp'] - points[0]['timeStamp']

    points.append({**points[-1], **{
        'homeScoreLabel': None,
        'awayScoreLabel': None
    }})

    if teams['away']['name'] == statsGame['home_name']:
        temp = teams['away']
        teams['away'] = teams['home']
        teams['home'] = temp

    points = pd.DataF   rame(points)

    renamings = {}
    for col in list(points.columns):
        newName = col.replace('homeScore', teams['home']['display_code']).replace(
            'awayScore', teams['away']['display_code'])
        if col != newName:
            renamings[col] = newName

    points = points.rename(
        columns=renamings)

    try:
        start = datetime.strptime(
            points['timeStamp'].iloc[0], "%Y-%m-%dT%H:%M:%S.%fZ")
    except:
        start = datetime.strptime(
            points['timeStamp'].iloc[0], "%Y-%m-%dT%H:%M:%SZ")

    try:
        end = datetime.strptime(
            points['timeStamp'].iloc[-1], "%Y-%m-%dT%H:%M:%S.%fZ")
    except:
        end = datetime.strptime(
            points['timeStamp'].iloc[-1], "%Y-%m-%dT%H:%M:%SZ")

    delta = end - start

    points['timeStamp'].iloc[-1] = (end +
                                    delta * 0.03).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    # points['timeStamp'][-1] = points['timeStamp'][-2] + timeRange * 0.2
    print(points)

    points = points.set_index('timeStamp')
    points.index = pd.to_datetime(
        points.index).tz_convert('US/Eastern')

    cmap = {}
    cmap[teams['home']['display_code']] = teams['home']['primary']
    cmap[teams['away']['display_code']] = teams['away']['primary']

    return plotLines([points], xLabel='Time (US/Eastern)', yLabel='Runs', title=f"{teams['away']['display_code']} at {teams['home']['display_code']} Runs over Time, {date}", cmap=cmap)
