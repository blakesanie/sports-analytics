from overTime import runsOverGame
from game import getPlayByPlay
print(runsOverGame('Nationals', 'Mets', '05/30/2022', battingStats=['runs'], pitchingStats=['pitcherCount'], markerLine='runs', xLabel="Time (US/Eastern)", yLabel="Runs", title="Runs over Time", legendLocation='upper left', legendCoords=(0.5, 0.27), awayColor='#990003', twitterLocation=(0.24, 0.97)))

# print(getPlayByPlay(661486))

# xLabel='Time (US/Eastern)', yLabel='Runs', title=f"{teams['away']['display_code']} at {teams['home']['display_code']} Runs over Time, {date}", cmap=cmap)
