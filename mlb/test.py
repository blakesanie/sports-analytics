from overTime import runsOverGame
from game import getPlayByPlay

print(runsOverGame('Rockies', 'Nationals', '05/28/2022', battingStats=['runs', 'hits'], xLabel="Time (US/Eastern)", yLabel="Runs", title="Runs over Time", legendLocation='upper left'))

# print(getPlayByPlay(661486))

# xLabel='Time (US/Eastern)', yLabel='Runs', title=f"{teams['away']['display_code']} at {teams['home']['display_code']} Runs over Time, {date}", cmap=cmap)
