import statsapi
import mlbgame
import pandas as pd

teams = pd.DataFrame(statsapi.lookup_team(''))

mlbTeams = pd.DataFrame([dict(zip(dir(team), [getattr(team, attr) for attr in dir(team)]))
                         for team in mlbgame.teams()])

teams = teams.merge(mlbTeams[['club', 'division',
                              'league', 'primary', 'team_id', 'display_code']], how='inner', left_on='id', right_on='team_id')

teams = teams.drop('team_id', axis=1)
teams['display_code'] = teams['display_code'].str.upper()


def getTeamCols(teamName, columns=['id']):
    return teams.loc[teams['teamName'] == teamName][columns].values[0]

