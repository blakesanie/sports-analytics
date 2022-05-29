import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FixedLocator
import matplotlib.dates as mdates
import matplotlib.patheffects as path_effects
matplotlib.rcParams['timezone'] = 'US/Eastern'
import re
import datetime as datetime


def plotLines(dfs, title=None, xLabel=None, yLabel=None, cmap={}, legendLocation='lower right', innings=None, inningsMarkers=[], dateFormatStr='%-I:%M%p', league='mlb', lineThickness=4.0):

    fig, axes = plt.subplots(1, 1)
    fig.set_figheight(5)
    fig.set_figwidth(5)
    fig.set_dpi(1080/5)
    if league == 'mlb':
        axes.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0,15,30,45], interval = 4))
        axes.xaxis.set_major_formatter(
            mdates.DateFormatter(dateFormatStr))
    elif league == 'nba':
        axes.xaxis.set_major_locator(FixedLocator([i * 60 for i in range(0, 49, 6)]))

        def strfdelta(x, fmt):
            x = int(x)
            return f"{x // 60}:{(x % 60):02}"

        formatter = matplotlib.ticker.FuncFormatter(strfdelta)
        axes.xaxis.set_major_formatter(formatter)


    plt.xticks(fontsize=9)
    # axes.set_yticks()
    axes.yaxis.tick_right()
    axes.yaxis.set_label_position("right")
    axes.tick_params(axis='y', length=0)
    axes.yaxis.set_major_locator(MaxNLocator(16, integer=True))
    plt.yticks(fontsize=9)
    # axes.yaxis.set_ticks([])

    # axes.xaxis.tick_top()
    # axes.xaxis.set_label_position("top")

    team1, team2 = list(cmap.keys())
    reversecmap = {}
    reversecmap[team1] = cmap[team2]
    reversecmap[team2] = cmap[team1]

    labels = []

    newPitcherMarkerMade = False
    for df in dfs:
        cols = list(df.columns)
        textOffsetX = (df.index[-1] - df.index[0]) * 0.018
        numLines = 0
        for col in cols:
            team = col.split(' ')[0]
            opponent = team2 if team == team1 else team1
            if col.endswith('Label'):
                # axes.text()
                for i in range(len(df[col])):
                    if df[col][i] and not pd.isnull(df[col][i]):
                        print('axis text', df[col][i])
                        colWithoutLabel = col.replace(
                            ' Label', '')
                        txt = axes.text(df.index[i], df[colWithoutLabel][i], df[col][i], ha='right', va='bottom', fontsize=9)  # backgroundcolor='#ffffffc0'

                        txt.set_path_effects([path_effects.Stroke(linewidth=2, foreground='white'),
                                              path_effects.Normal()])

                        labels.append(txt)
            elif col.endswith('Pitchers Faced'):
                if not newPitcherMarkerMade:
                    axes.plot([], [], marker='o', c='black', label='New Pitcher', ls='none', alpha=0.2, markersize=5)
                    newPitcherMarkerMade = True
                pitchingChanges = df[df[col].notnull()]
                markers = axes.plot(pitchingChanges.index, pitchingChanges[cols[0]], marker='o', c=reversecmap.get(team, 'black'), ls='none', markersize=5, alpha=0.8)
                for marker in markers:
                    marker.set_path_effects([path_effects.Stroke(linewidth=4, foreground='white'),
                                      path_effects.Normal()])
            elif col.endswith('Timeout'):
                if not newPitcherMarkerMade:
                    axes.plot([], [], marker='o', c='white', label='Timeout', ls='none', alpha=1, markersize=8, markeredgecolor='black')
                    newPitcherMarkerMade = True
                timeouts = df[df[col].notnull()]
                markers = axes.plot(timeouts.index, timeouts[cols[0]], marker='o', c='white', ls='none', markersize=8, alpha=1, markeredgecolor=cmap.get(team, 'black'))

            else:
                axes.step(df.index, df[col], cmap.get(team, 'black'), where='post',
                          label=col, alpha=0.8, linewidth=lineThickness - numLines * 2, ls='-' if numLines == 0 else '--')
                numLines += 1
    if xLabel:
        axes.set_xlabel(xLabel)
    if yLabel:
        axes.set_ylabel(yLabel)
    if title:
        axes.set_title(title)

    minY, maxY = axes.get_ylim()
    yRange = maxY - minY
    if league == 'mlb':
        plt.ylim(minY - yRange * 0.06, maxY)

    plt.gca().set_yticks([tick for tick in plt.gca().get_yticks() if tick >=0])
    for txt in labels:
        txt.set_y(txt._y + yRange * 0.005)

    if innings is not None:
        if not isinstance(innings, list):
            innings = innings.index
        for x in innings:
            axes.axvline(x=x, c='black', ls='--', lw=0.7, alpha=0.16)

    i = 0
    for x, txt in inningsMarkers:
        axes.text(x, minY - yRange * 0.02 + yRange * 0.003 * (1 if i % 2 == 0 else -1), txt, ha='center', va='top' if i % 2 == 1 else 'bottom', fontsize=7)
        i += 1

        # axes.text(x, y, text)
    axes.legend(loc=legendLocation, prop={'size': 9})
    axes.spines['top'].set_visible(False)
    axes.spines['right'].set_visible(False)
    axes.spines['bottom'].set_visible(False)
    axes.spines['left'].set_visible(False)
    plt.tight_layout()
    # axes.tick_params(axis='x', which='major', top=15)
    # plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
    plt.show()
