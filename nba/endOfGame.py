import pandas as pd

from game import getGame, getTeamsFromGame, formatDate
from nba_api.live.nba.endpoints import boxscore
import matplotlib.pyplot as plt


if __name__ == '__main__':
    team = 'Celtics'
    date = '2022-05-29'
    color = 'green'
    opponentColor = 'red'
    stats = ['points', 'assists', 'rebounds']
    game = getGame(team=team, date=date)
    box = boxscore.BoxScore(game['GAME_ID']).game.get_dict()

    homePlayers = []
    for player in box['homeTeam']['players']:
        d = {**player, **player['statistics']}
        del d['statistics']
        homePlayers.append(d)

    homeDf = pd.DataFrame(homePlayers)

    awayPlayers = []
    for player in box['awayTeam']['players']:
        d = {**player, **player['statistics']}
        del d['statistics']
        awayPlayers.append(d)

    awayDf = pd.DataFrame(awayPlayers)

    fig = plt.figure()
    fig.set_figheight(5)
    fig.set_figwidth(5)
    fig.set_dpi(1080 / 5)
    ax = fig.add_subplot(projection='3d')

    colors = [color, opponentColor]
    if box['awayTeam']['teamName'] == team:
        colors.reverse()
    dfs = [homeDf, awayDf]
    annotations = []
    for i, df in enumerate(dfs):
        df['minutes'] = df['minutesCalculated'].str.slice(start=2, stop=4).astype(int)
        df = df[df['minutes'] > 3]
        df['rebounds'] = df['reboundsDefensive'] + df['reboundsOffensive']
        dfs[i] = df

        ax.scatter(*[df[stat] for stat in stats], marker='o', c=colors[i], s=10.0, label= box['homeTeam']['teamTricode'] if i == 0 else box['awayTeam']['teamTricode'])
        for row in df.to_dict(orient="records"):
            annotations.append(ax.text(*[row[stat] for stat in stats], f"{row['familyName']}\n{', '.join([str(row[stat]) for stat in stats])}\n\n\n", size=6, zorder=1,
                    color='black', ha='center', va='center'))
            # ax.annotate(row['familyName'], )

    minZ, maxZ = ax.get_zlim()
    zRange = maxZ - minZ
    for txt in annotations:
        # txt.set_3d_properties(txt._position3d[-1] + zRange* 0.4)
        # txt.set_rotation(90)
        pos = txt._position3d
        pos[-1] += 0.51
        txt.set_position(pos)
        # txt._position3d[-1] += zRange * 0.4
        #set_position
        # txt.set_3d_properties(properties)

    stats = [stat.title() for stat in stats]

    ax.set_xlabel(stats[0])
    ax.set_ylabel(stats[1])
    ax.set_zlabel(stats[2])
    ax.invert_xaxis()
    plt.title(f"{game['MATCHUP']}, {formatDate(date)}\n{' - '.join(stats)}", y=1.03, linespacing=1.8)
    # plt.tight_layout()
    plt.subplots_adjust(left=-0.13, bottom=0.02, top=0.93, right=1)
    ax.text2D(0.99, 0.87, '@blakesanie', ha='right', va='top', alpha=0.6, transform=ax.transAxes)
    ax.legend()
    plt.show()
    pass


