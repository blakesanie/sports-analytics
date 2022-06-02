import statsapi
import mlbgame
import pandas as pd

if __name__ == "__main__":

    teams = pd.DataFrame(statsapi.lookup_team(""))

    mlbTeams = pd.DataFrame(
        [
            dict(zip(dir(team), [getattr(team, attr) for attr in dir(team)]))
            for team in mlbgame.teams()
        ]
    )

    teams = teams.merge(
        mlbTeams[["club", "division", "league", "primary", "team_id", "display_code"]],
        how="inner",
        left_on="id",
        right_on="team_id",
    )

    teams = teams.drop("team_id", axis=1)
    teams["display_code"] = teams["display_code"].str.upper()

    teams = teams.drop(["teamCode", "fileCode", "club"], axis=1)

    twitterData = pd.DataFrame(
        [
            ("SF", "SFGiants", "SFGiants SFG"),
            ("SD", "Padres", "TimeToShine Padres"),
            ("LAD", "Dodgers", "Dodgers LAD"),
            ("ARI", "Dbacks", "Dbacks"),
            ("COL", "Rockies", "Rockies"),
            ("NYM", "Mets", "LGM NYM Mets"),
            ("ATL", "Braves", "ForTheA Braves"),
            ("PHI", "Phillies", "RingTheBell Phillies"),
            ("MIA", "Marlins", "MakeItMiami Marlins"),
            ("WSH", "Nationals", "NATITUDE Nationals"),
            ("MIL", "Brewers", "ThisIsMyCrew BrewCrew Brewers"),
            ("STL", "Cardinals", "STLCards Cardinals"),
            ("PIT", "Pirates", "RaiseIt LetsGoBucs Pirates"),
            ("CHC", "Cubs", "Cubs Cubbies"),
            ("CIN", "REDS", "ATOBTTR Reds"),
            ("NYY", "Yankees", "RepBX Yankees NYY BronxBombers"),
            ("BOS", "RedSox", "DirtyWater RedSox"),
            ("TOR", "BlueJays", "NextLevel BlueJays"),
            ("BAL", "Orioles", "Birdland Orioles"),
            ("TB", "RaysBaseball", "RaysUp Rays"),
            ("MIN", "Twins", "MNTwins"),
            ("CWS", "whitesox", "ChangeTheGame WhiteSox"),
            ("CLE", "CleGuardians", "ForTheLand Guardians"),
            ("DET", "tigers", "DetroitRoots Tigers"),
            ("KC", "Royals", "RoyalsAssist Royals"),
            ("HOU", "astros", "LevelUp Astros"),
            ("LAA", "Angels", "GoHalos Angels"),
            ("TEX", "Rangers", "StraightUpTX Rangers"),
            ("SEA", "Mariners", "SeaUsRise Mariners"),
            ("OAK", "Athletics", "RootedInOakland DrumTogether Athletics As"),
        ],
        columns=["display_code", "twitterHandle", "hashtags"],
    )

    teams = teams.merge(twitterData, left_on="display_code", right_on="display_code")

    teams = teams.set_index("id")

    teams.to_csv("teams.csv")
    print("generated teams.csv")
else:
    try:
        teams = pd.read_csv("./teams.csv")
    except FileNotFoundError as e:
        raise Exception(
            "teams.csv not found. Run python teams.py to generate this file"
        )


def getTeamColsByName(teamName, type="short", columns=["id"]):
    return teams.loc[teams["teamName" if type == "short" else "name"] == teamName][
        columns
    ].values[0]


def getTwitterInfoByFullName(name):
    out = teams.loc[name == teams["name"]]
    return "@" + out["twitterHandle"].values[0], " ".join(
        ["#" + tag for tag in out["hashtags"].values[0].split(" ")]
    )
