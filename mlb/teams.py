import statsapi
import mlbgame
import pandas as pd

if __name__ == '__main__':

    teams = pd.DataFrame(statsapi.lookup_team(''))

    mlbTeams = pd.DataFrame([dict(zip(dir(team), [getattr(team, attr) for attr in dir(team)]))
                             for team in mlbgame.teams()])

    teams = teams.merge(mlbTeams[['club', 'division',
                                  'league', 'primary', 'team_id', 'display_code']], how='inner', left_on='id',
                        right_on='team_id')

    teams = teams.drop('team_id', axis=1)
    teams['display_code'] = teams['display_code'].str.upper()

    teams = teams.drop(['teamCode', 'fileCode', 'club'], axis=1)
    teams = teams.set_index('id')

    twitterData = [
        ('SFG', 'SFGiants', 'SFGiants'),
        ('SDP', 'Padres', 'TimeToShine'),
        ('LAD', 'Dodgers', 'Dodgers')
    ]

    teams.to_csv('teams.csv')
    print('generated teams.csv')
else:
    try:
        teams = pd.read_csv('./teams.csv')
    except FileNotFoundError as e:
        raise Exception('teams.csv not found. Run python teams.py to generate this file')


def getTeamColsByName(teamName, type='short', columns=['id']):
    return teams.loc[teams['teamName' if type == 'short' else 'name'] == teamName][columns].values[0]


