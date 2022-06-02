from nba_api.stats.static import teams
import pandas as pd

teams = pd.DataFrame(teams.get_teams())

print(teams)
