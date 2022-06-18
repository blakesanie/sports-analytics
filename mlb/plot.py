import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, FixedLocator
import matplotlib.dates as mdates
import matplotlib.patheffects as path_effects
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

matplotlib.rcParams["timezone"] = "US/Eastern"


def plotLines(
    dfs,
    title=None,
    xLabel=None,
    yLabel=None,
    cmap={},
    amap={},
    legendLocation="lower right",
    innings=None,
    inningsMarkers=[],
    dateFormatStr="%-I:%M%p",
    league="mlb",
    lineThickness=4.0,
    notes=[],
    legendCoords=None,
    twitterLocation=None,
    bang=None,
):

    fig, axes = plt.subplots(1, 1)
    fig.set_figheight(5)
    fig.set_figwidth(5)
    fig.set_dpi(1080 / 5)
    if league == "mlb":
        axes.xaxis.set_major_locator(
            mdates.MinuteLocator(byminute=[0, 15, 30, 45], interval=4)
        )
        axes.xaxis.set_major_formatter(mdates.DateFormatter(dateFormatStr))
    elif league == "nba":
        axes.grid(axis="y", alpha=0.3)
        axes.xaxis.set_major_locator(FixedLocator([i * 60 for i in range(0, 49, 6)]))

        def strfdelta(x, fmt):
            x = int(x)
            return f"{x // 60}:{(x % 60):02}"

        formatter = matplotlib.ticker.FuncFormatter(strfdelta)
        axes.xaxis.set_major_formatter(formatter)

    plt.xticks(fontsize=9)
    axes.yaxis.tick_right()
    axes.yaxis.set_label_position("right")
    axes.tick_params(axis="y", length=0)
    axes.yaxis.set_major_locator(MaxNLocator(16, integer=True))
    plt.yticks(fontsize=9)

    team1, team2 = list(cmap.keys())
    reversecmap = {}
    reversecmap[team1] = cmap[team2]
    reversecmap[team2] = cmap[team1]

    labels = []

    markersDrawn = set([])

    seriesMax = -float("inf")
    seriesMaxX = None
    seriesMaxTeam = None

    for colI in range(1000):
        numDfsParsed = 0
        for df in dfs:
            cols = df.columns
            if colI < len(cols):
                numDfsParsed += 1
                col = cols[colI]
                team = col.split(" ")[0]
                opponent = list(cmap.keys())
                opponent.remove(team)
                opponent = opponent[0]
                if col.endswith("Label"):
                    for i in range(len(df[col])):
                        if df[col][i] and not pd.isnull(df[col][i]):
                            print("axis text", df[col][i])
                            colWithoutLabel = col.replace(" Label", "")
                            txt = axes.text(
                                df.index[i],
                                df[colWithoutLabel][i],
                                df[col][i] + " ",
                                ha="right",
                                va="center",
                                fontsize=7,
                                zorder=5,
                            )

                            txt.set_path_effects(
                                [
                                    path_effects.Stroke(
                                        linewidth=2, foreground="white"
                                    ),
                                    path_effects.Normal(),
                                ]
                            )

                            labels.append((team, txt))
                elif col.endswith("Pitchers Faced"):
                    if "Pitchers Faced" not in markersDrawn:
                        axes.plot(
                            [],
                            [],
                            marker="o",
                            c="black",
                            label="New Pitcher",
                            ls="none",
                            alpha=0.2,
                            markersize=5,
                        )
                        markersDrawn.add("Pitchers Faced")
                    pitchingChanges = df[df[col].notnull()]
                    markers = axes.plot(
                        pitchingChanges.index,
                        pitchingChanges[cols[0]],
                        marker="o",
                        c=reversecmap.get(team, "black"),
                        ls="none",
                        markersize=lineThickness,
                        alpha=amap.get(opponent, 1) * 0.8,
                    )
                    for marker in markers:
                        marker.set_path_effects(
                            [
                                path_effects.Stroke(linewidth=4, foreground="white"),
                                path_effects.Normal(),
                            ]
                        )
                elif col.endswith("Timeout"):
                    if "Timeout" not in markersDrawn:
                        axes.plot(
                            [],
                            [],
                            marker="o",
                            c="white",
                            label="Timeout",
                            ls="none",
                            alpha=1,
                            markersize=5,
                            markeredgecolor="black",
                        )
                        markersDrawn.add("Timeout")
                    timeouts = df[df[col].notnull()]
                    axes.plot(
                        timeouts.index,
                        timeouts[cols[0]],
                        marker="o",
                        c="white",
                        ls="none",
                        markersize=5,
                        alpha=1,
                        markeredgecolor=cmap.get(team, "black"),
                    )

                else:
                    label = col
                    if col.endswith("Runs") or col.endswith("Score"):
                        label += f" (F: {round(df[col].iloc[-1])})"
                    for k in range(10):
                        axes.step(
                            df.index,
                            df[col],
                            c=cmap.get(team, "black") if k == 0 else "none",
                            where="post",
                            label=label if k == 0 else None,
                            alpha=amap.get(team, 1) * 0.8,
                            linewidth=lineThickness - colI * 2,
                            ls="-" if colI == 0 else "--",
                        )
                        if league == "mlb":
                            changeMask = df[col].diff() != 0
                            axes.plot(
                                df.index[changeMask][1:],
                                df[col][changeMask][1:],
                                ls="none",
                                c="none",
                                marker="o",
                                mfc="w",
                                mec="none",
                                ms=2,
                                zorder=3,
                            )
                        max = df[col].max()
                        if max > seriesMax:
                            seriesMax = max
                            seriesMaxX = df.index[df[col].argmax()]
                            seriesMaxTeam = team

        if numDfsParsed == 0:
            break

    if bang:
        im = OffsetImage(plt.imread("bang.png"), zoom=0.08, zorder=2)
        ab = AnnotationBbox(im, bang, xycoords="data", frameon=False)
        axes.add_artist(ab)

    if xLabel:
        axes.set_xlabel(xLabel)
    if yLabel:
        axes.set_ylabel(yLabel)
    if title:
        axes.set_title(title)

    minY, maxY = axes.get_ylim()
    yRange = maxY - minY

    minX, maxX = axes.get_xlim()
    xRange = maxX - minX

    if notes is not None and len(notes) > 0:
        axes.text(
            0,
            0.98,
            "\n".join(notes),
            ha="left",
            va="top",
            linespacing=1.8,
            transform=axes.transAxes,
        )

    if league == "mlb":
        plt.ylim(minY - yRange * 0.06, maxY)
        axes.text(
            *((0.5, 1) if twitterLocation is None else twitterLocation),
            "@blakesanie",
            ha="center",
            va="top",
            alpha=0.6,
            transform=axes.transAxes,
            fontsize=6,
            bbox=dict(facecolor="white", alpha=1, edgecolor="none"),
        )
        for _ in range(10):
            axes.plot(
                [0.42, 0.58], [0.98, 0.98], transform=axes.transAxes, color="none"
            )
            axes.plot(
                [seriesMaxX, df.index[-1]],
                [seriesMax + yRange * 0.02, seriesMax + yRange * 0.02],
                c="none",
            )
    else:
        axes.text(
            0.5,
            0.98,
            "@blakesanie",
            ha="center",
            va="top",
            alpha=0.6,
            transform=axes.transAxes,
        )

    plt.gca().set_yticks([tick for tick in plt.gca().get_yticks() if tick >= 0])
    for team, txt in labels:
        txt.set_va("top" if team == seriesMaxTeam else "bottom")
        txt.set_y(txt._y + yRange * (-0.009 if team == seriesMaxTeam else 0.005))

    if innings is not None:
        if not isinstance(innings, list):
            innings = innings.index
        for x in innings:
            axes.axvline(
                x=x, c="black", ls="--", lw=1 if league == "mlb" else 1.5, alpha=0.15
            )

    for i in range(10):
        axes.axhline(y=minY, color="none")  # draw lines so the legend doesnt go here

    i = 0
    for x, txt in inningsMarkers:
        axes.text(
            x,
            minY - yRange * 0.02 + yRange * 0.003 * (1 if i % 2 == 0 else -1),
            txt,
            ha="center",
            va="top" if i % 2 == 1 else "bottom",
            fontsize=7,
        )
        i += 1

    axes.legend(loc=legendLocation, prop={"size": 8}, bbox_to_anchor=legendCoords)
    axes.spines["top"].set_visible(False)
    axes.spines["right"].set_visible(False)
    axes.spines["bottom"].set_visible(False)
    axes.spines["left"].set_visible(False)
    plt.tight_layout()
    plt.show()
    filename = f'./plots/{title.split(",")[0]}.png'
    fig.savefig(filename)
    return filename
