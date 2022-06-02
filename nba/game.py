import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.endpoints import playbyplayv2
from teams import teams
from mlb.plot import plotLines
import numpy as np
from datetime import datetime
import itertools


def getGame(date="2022-05-27", team="Celtics"):
    teamId = teams.loc[teams["nickname"] == team]["id"].values[0]
    gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=teamId)
    # The first DataFrame of those returned is what we want.
    games = gamefinder.get_data_frames()[0]
    onDate = games.loc[games["GAME_DATE"] == date]

    return onDate.loc[0].to_dict()


def getPlayByPlay(gameId):
    pbp = playbyplayv2.PlayByPlayV2(gameId)
    pbp = pbp.get_data_frames()[0]
    return pbp


def getGameStopwatch(periodSeries, timeStringSeries):
    pass


def getTeamsFromGame(game):
    matchupSplit = game["MATCHUP"].split(" ")
    return set([matchupSplit[0], matchupSplit[-1]])


def getTimouts(pbp):
    filled = pbp.copy()
    # filled['SCORE'] = filled['SCORE']
    filled["SCORE"] = filled["SCORE"].fillna(method="ffill")
    homeTimeouts = filled.loc[
        pbp["HOMEDESCRIPTION"].str.contains("Timeout").fillna(False)
    ]
    homeTeam = homeTimeouts.iloc[0]["HOMEDESCRIPTION"].split(" ")[0]
    homeTeam = homeTeam[0] + homeTeam[1:].lower()
    homeAbbr = teams[teams["nickname"] == homeTeam].iloc[0]["abbreviation"]
    homeTimeouts[f"{homeAbbr} Timeout"] = 1
    homeTimeouts = homeTimeouts[["SCORE", f"{homeAbbr} Timeout"]]

    visitorTimeouts = filled.loc[
        pbp["VISITORDESCRIPTION"].str.contains("Timeout").fillna(False)
    ]
    visitorTeam = visitorTimeouts.iloc[0]["VISITORDESCRIPTION"].split(" ")[0]
    visitorTeam = visitorTeam[0] + visitorTeam[1:].lower()
    visitorAbbr = teams[teams["nickname"] == visitorTeam].iloc[0]["abbreviation"]
    visitorTimeouts[f"{visitorAbbr} Timeout"] = 1
    visitorTimeouts = visitorTimeouts[["SCORE", f"{visitorAbbr} Timeout"]]

    return pd.concat((homeTimeouts, visitorTimeouts))


def convertScoringToRate(df):
    df = df.merge(
        pd.DataFrame(index=np.arange(60 * 48), data=None),
        how="outer",
        left_index=True,
        right_index=True,
    )
    df[df.columns[0]] = df[df.columns[0]].fillna(method="ffill")
    original = df.copy()
    minutes = 5
    df[df.columns[0]] = df[df.columns[0]].diff(periods=minutes * 60) / minutes
    df[df.columns[0]][: minutes * 60] = original[df.columns[0]][: minutes * 60] / (
        np.arange(minutes * 60) / 60
    )
    df[df.columns[0]] = df[df.columns[0]].rolling(30).mean()
    df = df.rename(
        columns={f"{df.columns[0]}": df.columns[0].split(" ")[0] + " Scoring Rate"}
    )

    return df


def getScores(game, pbp):
    out = pbp.loc[(pbp["SCORE"].notnull()) | (pbp["EVENTMSGTYPE"] == 12)]
    out["SCORE"] = out["SCORE"].fillna("0 - 0")

    timeouts = getTimouts(pbp)
    out = out.merge(timeouts, how="left", left_on="SCORE", right_on="SCORE")

    gameTeams = getTeamsFromGame(game)

    firstScore = out.iloc[1]
    scoringTeam = out.iloc[1]["PLAYER1_TEAM_ABBREVIATION"]
    gameTeams.remove(scoringTeam)
    losingTeam = list(gameTeams)[0]
    scoreSplit = firstScore["SCORE"].split(" ")
    if int(scoreSplit[0]) > int(scoreSplit[-1]):
        team1 = scoringTeam
        team2 = losingTeam
    else:
        team2 = scoringTeam
        team1 = losingTeam

    # allScores = out[['SCORE', 'PERIOD', 'PCTIMESTRING']]
    allScores = out
    allScores[["minutesRemaining", "secondsRemaining"]] = allScores[
        "PCTIMESTRING"
    ].str.split(":", 1, expand=True)
    allScores["secondsPlayed"] = (12 * 60 * allScores["PERIOD"].astype(int)) - (
        allScores["secondsRemaining"].astype(int)
        + allScores["minutesRemaining"].astype(int) * 60
    ).astype(int)
    teamCols = [f"{team1} Score", f"{team2} Score"]
    allScores[teamCols] = allScores["SCORE"].str.split(" - ", 1, expand=True)
    allScores[teamCols] = allScores[teamCols].astype(int)
    out = allScores[
        [*teamCols, "secondsPlayed", f"{team1} Timeout", f"{team2} Timeout"]
    ].drop_duplicates()
    # out['secondsPlayed'] = pd.to_timedelta(out['secondsPlayed'], unit='seconds')
    out = out.set_index("secondsPlayed")

    out = out.drop_duplicates()

    return (
        out,
        out[[col for col in out.columns if col.startswith(team1)]],
        out[[col for col in out.columns if col.startswith(team2)]],
    )


def formatDate(date):
    year = date[:4]
    month = int(date[5:7])
    day = int(date[-2])
    return f"{month}/{day}/{year}"


def getScoringNotes(gameTeams, scoringData):
    out = []
    diff = scoringData[f"{gameTeams[0]} Score"] - scoringData[f"{gameTeams[1]} Score"]
    team1Lead = diff.max()
    team2Lead = -diff.min()
    out.append(f"{gameTeams[0]} Max Lead: {team1Lead}")
    out.append(f"{gameTeams[1]} Max Lead: {team2Lead}")
    leadChanges = len(list(itertools.groupby(diff[diff != 0], lambda x: x > 0))) - 1
    out.append(f"Total Lead Changes: {leadChanges}")
    return out


if __name__ == "__main__":
    team = "Celtics"
    date = "2022-05-29"
    color = "green"
    opponentColor = "red"
    game = getGame(team=team, date=date)
    gameTeams = list(getTeamsFromGame(game))
    print(game)
    pbp = getPlayByPlay(game["GAME_ID"])
    allScoring, team1Scoring, team2Scoring = getScores(game, pbp)

    notes = getScoringNotes(gameTeams, allScoring)

    formattedDate = formatDate(date)

    cmap = {
        f"{gameTeams[0]}": color
        if gameTeams[0] == game["TEAM_ABBREVIATION"]
        else opponentColor,
        f"{gameTeams[1]}": color
        if gameTeams[1] == game["TEAM_ABBREVIATION"]
        else opponentColor,
    }

    plotLines(
        [team1Scoring, team2Scoring],
        cmap=cmap,
        title=f"{game['MATCHUP']}, {formattedDate}, Points over Time",
        xLabel="Game Time Elapsed",
        yLabel="Points",
        league="nba",
        lineThickness=2,
        dateFormatStr="%S",
        legendLocation="lower right",
        innings=[0, 12 * 60, 24 * 60, 36 * 60, 48 * 60],
        notes=notes,
    )

    team1Scoring = convertScoringToRate(team1Scoring)
    team2Scoring = convertScoringToRate(team2Scoring)

    plotLines(
        [team1Scoring, team2Scoring],
        cmap=cmap,
        title=f"{game['MATCHUP']}, {formattedDate}, Scoring Rates over Time",
        xLabel="Game Time Elapsed",
        yLabel="Points / Minute (over 5 Minutes)",
        league="nba",
        lineThickness=2,
        dateFormatStr="%S",
        legendLocation="lower center",
        innings=[0, 12 * 60, 24 * 60, 36 * 60, 48 * 60],
    )
