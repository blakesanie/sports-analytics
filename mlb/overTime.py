import pandas as pd
from datetime import datetime, timezone
from teams import getTeamColsByName, getTwitterInfoByFullName, getLocationByFullName
from game import getGame, getScoringPlays, getPlayByPlay
from plot import plotLines
import pytz
import re
from color import color_similarity
import math
import random
from string import punctuation


def camel_case_split(identifier):
    matches = re.finditer(
        ".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", identifier
    )
    return " ".join([m.group(0) for m in matches])


def capitalize(string):
    sentence = " ".join(camel_case_split(word) for word in string.split(" "))
    return " ".join(word[0].title() + word[1:] for word in sentence.split(" "))


def getPitchingChanges(pitching):
    return pitching.loc[pitching["pitcherCount"].diff() != 0][1:]


def getInningTimeStamps(pitching, homePitching=None, awayInningChanges=None):
    inningsPitched = pitching["inningsPitched"].astype(float)
    outChanges = pitching.loc[inningsPitched.diff() != 0]
    outChanges = outChanges[1:]  # remove 0 outs at start of game
    outChanges["inningsPitched"] = outChanges["inningsPitched"].astype(float)
    isWalkOff = False
    if homePitching is not None and awayInningChanges is not None:
        homeInningsPitched = awayInningChanges["inningsPitched"].max()
        lastEndOfTopTimeStamp = awayInningChanges.index[-1]
        awayScore = homePitching["runs"].max()
        homeScore = pitching["runs"].max()
        winningRuns = pitching[pitching["runs"] > awayScore]
        if len(winningRuns) > 0:
            lastHomeRunScoredTimeStamp = winningRuns.index[0]
            if (
                homeInningsPitched >= 9
                and homeScore > awayScore
                and lastHomeRunScoredTimeStamp > lastEndOfTopTimeStamp
            ):
                lastRow = pitching.iloc[-1]
                lastRow["inningsPitched"] = math.ceil(float(lastRow["inningsPitched"]))
                outChanges = outChanges.append(lastRow)
                isWalkOff = True
    inningsPitched = outChanges["inningsPitched"]
    inningChanges = outChanges.loc[inningsPitched % 1 == 0]
    return outChanges, inningChanges, isWalkOff


def specialPitchingPerformance(homePitching, awayPitching):
    for df in (homePitching, awayPitching):
        if df.iloc[-1]["hits"] == 0:
            if df.iloc[-1]["obp"] == 0:
                return "Perfect Game ????! "
            return "No-hitter ????! "
    return ""


def getFirstPitchTime(pitching):
    return pitching.loc[pitching["pitchesThrown"] >= 1].index[0]


def runsOverGame(
    teamName1,
    teamName2,
    date,
    game=None,
    pbp=None,
    gameIndex=0,
    battingStats=[],
    pitchingStats=[],
    xLabel=None,
    yLabel=None,
    title=None,
    legendLocation="lower right",
    markerLine=None,
    homeColor=None,
    awayColor=None,
    twitterLocation=None,
    legendCoords=None,
):
    cols = ["id", "primary", "secondary", "name", "display_code", "teamName"]
    if game is None:
        teams = {
            "away": dict(zip(cols, getTeamColsByName(teamName1, columns=cols))),
            "home": dict(zip(cols, getTeamColsByName(teamName2, columns=cols))),
        }
        statsGame = getGame(
            teams["away"]["id"], teams["home"]["id"], date, gameIndex=gameIndex
        )
        if statsGame["away_name"] != teams["away"]["name"]:
            temp = teams["away"]
            teams["away"] = teams["home"]
            teams["home"] = temp
    else:
        teams = {
            "away": dict(
                zip(
                    cols,
                    getTeamColsByName(game["away_name"], type="full", columns=cols),
                )
            ),
            "home": dict(
                zip(
                    cols,
                    getTeamColsByName(game["home_name"], type="full", columns=cols),
                )
            ),
        }
        statsGame = game

    homePitching, awayPitching, homeBatting, awayBatting = (
        getPlayByPlay(statsGame["game_id"]) if pbp is None else pbp
    )

    awayOutChanges, awayInningChanges, _ = getInningTimeStamps(homePitching)
    homeOutChanges, homeInningChanges, isWalkOff = getInningTimeStamps(
        awayPitching, homePitching=homePitching, awayInningChanges=awayInningChanges
    )

    starter = specialPitchingPerformance(awayPitching, homePitching)

    # parse startTime using pandas for consistency
    startTime = pd.DataFrame([{"startTime": statsGame["game_datetime"]}]).set_index(
        "startTime"
    )
    startTime.index = pd.to_datetime(startTime.index).tz_convert("US/Eastern")
    startTime = startTime.index[0]

    firstPitchTime = getFirstPitchTime(homePitching)

    startTime = max(startTime, firstPitchTime)

    allInnings = pd.concat((awayInningChanges, homeInningChanges))
    allInnings.loc[startTime] = 0  # ensure row for start of game (score tied, 0-0)
    allInnings = allInnings.sort_index()
    innings = allInnings[
        :-1
    ]  # game ends after last inning ends anyway, so no need to track when it ends

    inningsTimestamps = allInnings.index.values
    top = True
    inningsMarkers = []
    for i in range(1, len(inningsTimestamps)):
        inningsMarkers.append(
            (
                inningsTimestamps[i - 1]
                + (inningsTimestamps[i] - inningsTimestamps[i - 1]) / 2,
                f"{'T' if top else 'B'}{(i+1)//2}",
            )
        )
        top = not top

    innings = innings[1:]  # do not need line before T1

    print("potential battingStats:", homeBatting.columns)
    print("potential pitchingStats:", homePitching.columns)

    # the following dataframes will store the series (plural) to be plotted under a given color (hence team)
    homeDf = pd.DataFrame()
    awayDf = pd.DataFrame()

    if "runs" in battingStats:
        plays = getScoringPlays(statsGame["game_id"])

        homePoints = [{"timeStamp": statsGame["game_datetime"], "home runs": 0}]

        awayPoints = [{"timeStamp": statsGame["game_datetime"], "away runs": 0}]

        for play in plays["plays"]:
            # player's last name is second capitalized word in description (ignoring team name and other rules)
            capitalizedWordsEncountered = 0
            for word in (
                play["result"]["description"]
                .replace(teams["home"]["teamName"], "")
                .replace(teams["away"]["teamName"], "")
                .split(" ")
            ):
                if len(word) > 0 and word.lower() != word:
                    if capitalizedWordsEncountered == 1:  # if contains capital
                        lastName = word.strip(punctuation)
                        break
                    capitalizedWordsEncountered += 1
            if play["about"]["halfInning"] == "top":
                awayPoints.append(
                    {
                        "timeStamp": play["about"]["endTime"],
                        "away runs": play["result"]["awayScore"],
                        "away runs label": lastName,
                    }
                )
            else:
                homePoints.append(
                    {
                        "timeStamp": play["about"]["endTime"],
                        "home runs": play["result"]["homeScore"],
                        "home runs label": lastName,
                    }
                )

        homePoints = pd.DataFrame(homePoints)
        awayPoints = pd.DataFrame(awayPoints)

        homePoints = homePoints.set_index("timeStamp")
        homePoints.index = pd.to_datetime(homePoints.index).tz_convert("US/Eastern")

        awayPoints = awayPoints.set_index("timeStamp")
        awayPoints.index = pd.to_datetime(awayPoints.index).tz_convert("US/Eastern")

        homeDf = pd.concat((homeDf, homePoints))

        awayDf = pd.concat((awayDf, awayPoints))

    if "runs" in battingStats:
        battingStats.remove("runs")

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
        if "pitcherCount" in pitchingStats:
            homePitchingChanges = getPitchingChanges(awayPitching)[
                ["pitcherCount"]
            ].rename(columns={"pitcherCount": "home pitchers faced"})
            homeDf = pd.concat((homeDf, homePitchingChanges))

            awayPitchingChanges = getPitchingChanges(homePitching)[
                ["pitcherCount"]
            ].rename(columns={"pitcherCount": "away pitchers faced"})
            awayDf = pd.concat((awayDf, awayPitchingChanges))

            pitchingStats.remove("pitcherCount")

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
    cmap[teams["home"]["display_code"]] = (
        teams["home"]["primary"] if homeColor is None else homeColor
    )
    cmap[teams["away"]["display_code"]] = (
        teams["away"]["primary"] if awayColor is None else awayColor
    )

    similarity, lightest = color_similarity(*list(cmap.values()))

    amap = {}

    if similarity < 150:
        cmap[teams["away"]["display_code"]] = (
            teams["away"]["secondary"] if awayColor is None else awayColor
        )
        # for key, value in cmap.items():
        #     if value == lightest:
        #         amap[key] = 0.5 + similarity / 150 * 0.3
        #         break

    # if the game ends in a walk off, find the point (timestamp, runs) that corresponds
    walkOff = (
        (homeDf.index[homeDf["home runs"].argmax()], homeDf["home runs"].max())
        if isWalkOff
        else None
    )

    print(similarity, cmap)
    for i, df in enumerate(dfs):
        df = df.sort_index()
        df = df.loc[df.index >= startTime]
        if (
            markerLine
        ):  # the caller may scecify which line (series) the markers should be drawn over, which results in bringing that col to the front
            cols = list(df.columns)
            prefix = cols[0].split(" ")[0]
            newOrder = [prefix + " " + markerLine]
            for col in cols:
                if col != newOrder[0]:
                    newOrder.append(col)
            df = df[newOrder]
        renamings = {}
        for col in df.columns:
            if not (col.endswith("label") or col.endswith("pitchers faced")):
                # to keep data continuous, forward fill if not a moment-event saved for a discrete object, like a marker or label
                df[col] = df[col].fillna(method="ffill").fillna(0)
            newName = (
                col.replace(
                    "homeRun", "Home Run"
                )  # ensure that "homeRun" won't become "GiantsRun", for example
                .replace(
                    "home", teams["home"]["display_code"]
                )  # turn "home hits" into "SF hits"
                .replace("away", teams["away"]["display_code"])
            )
            newName = capitalize(
                newName
            )  # break up camelCased words and capitalize each word
            if col != newName:
                renamings[col] = newName
        dfs[i] = df.rename(columns=renamings)

    gameDate = statsGame["game_date"]
    year = int(gameDate[:4])
    month = int(gameDate[5:7])
    day = int(gameDate[-2:])

    doubleHeader = (
        ""
        if statsGame["doubleheader"] == "N"
        else f", Game {statsGame['game_num']} of 2"
    )

    filename = plotLines(
        dfs,
        xLabel=xLabel,
        yLabel=yLabel,
        title=f"{teams['away']['display_code']} @ {teams['home']['display_code']}{doubleHeader}, {month}/{day}/{year}{f', {title}' if title else ''}",
        cmap=cmap,
        amap=amap,
        legendLocation=legendLocation,
        innings=innings,
        inningsMarkers=inningsMarkers,
        legendCoords=legendCoords,
        twitterLocation=twitterLocation,
        bang=walkOff,
    )

    winningHandle, winningHashTags = getTwitterInfoByFullName(statsGame["winning_team"])
    losingHandle, losingHashTags = getTwitterInfoByFullName(statsGame["losing_team"])

    winningScore = max(statsGame["away_score"], statsGame["home_score"])
    losingScore = min(statsGame["away_score"], statsGame["home_score"])

    if isWalkOff:
        starter += "Walk off ????! "

    if winningScore - losingScore >= 10:
        starter += "Blowout ????! "

    message = [
        f"{starter}{statsGame['winning_team']} ({winningScore}) > {statsGame['losing_team']} ({losingScore}){doubleHeader}",
        f"{month}/{day}/{year} @ {statsGame['venue_name']}, {getLocationByFullName(statsGame['home_name'])}",
        f"{statsGame['winning_pitcher']} (W) > {statsGame['losing_pitcher']} (L)",
    ]

    if isinstance(statsGame["save_pitcher"], str):
        message.append(f"Save: {statsGame['save_pitcher']}")

    return filename, message
