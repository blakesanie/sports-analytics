from overTime import runsOverGame
from game import getPlayByPlay
print(runsOverGame('Yankees', 'Astros', '06/25/2022', gameIndex=0, battingStats=['runs'], pitchingStats=['pitcherCount'], markerLine='runs', xLabel="Time (US/Eastern)", yLabel="Runs", legendLocation='upper left', legendCoords=(0.5, 0.27), twitterLocation=(0.24, 0.97)))

# print(getPlayByPlay(661486))

# xLabel='Time (US/Eastern)', yLabel='Runs', title=f"{teams['away']['display_code']} at {teams['home']['display_code']} Runs over Time, {date}", cmap=cmap)
