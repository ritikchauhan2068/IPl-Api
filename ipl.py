import pandas as pd
import numpy as np
import json

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

# Load IPL match data and ball-by-ball data
matches = pd.read_csv('IPL_Matches_2008_2022 - IPL_Matches_2008_2022 (2).csv')
balls = pd.read_csv('IPL_Ball_by_Ball_2008_2022 - IPL_Ball_by_Ball_2008_2022.csv')

# Merge match and ball data
df = balls.merge(matches, on='ID', how='inner')

# Create a column for BowlingTeam
df['BowlingTeam'] = df.Team1 + df.Team2
df['BowlingTeam'] = df[['BowlingTeam', 'BattingTeam']].apply(lambda x: x.values[0].replace(x.values[1], ''), axis=1)

# Create batter_data with required columns
batter_data = df[np.append(balls.columns.values, ['BowlingTeam', 'Player_of_Match'])]

def season():
    seasons=list(matches['Season'].unique())
    seasonp={
        'seasons' : seasons
    }
    return seasonp


def teamsApi():
    teams = list(set(list(matches['Team1']) + list(matches['Team2'])))
    team_dict = {
        'teams': teams
    }
    return team_dict

def team_vs_team(team1, team2):
    temp_df = matches[(matches['Team1'] == team1) & (matches['Team2'] == team2) | (matches['Team1'] == team2) & (
                matches['Team2'] == team1)]
    total_matches = temp_df.shape[0]
    winning_team1 = temp_df['WinningTeam'].value_counts()[team1]
    winning_team2 = temp_df['WinningTeam'].value_counts()[team2]
    total_winning_matches = winning_team1 + winning_team2
    draw = total_matches - total_winning_matches
    response = {
        'total_matches': str(total_matches),
        team1: str(winning_team1),
        team2: str(winning_team2),
        'draw': str(draw)
    }
    return response

def allRecord(team):
    df = matches[(matches['Team1'] == team) | (matches['Team2'] == team)].copy()
    matches_played = df.shape[0]
    won = df[df.WinningTeam == team].shape[0]
    nr = df[df.WinningTeam.isnull()].shape[0]
    loss = matches_played - won - nr
    nt = df[(df.MatchNumber == 'Final') & (df.WinningTeam == team)].shape[0]
    return {
        'matchesplayed': matches_played,
        'won': won,
        'loss': loss,
        'noResult': nr,
        'title': nt
    }

def batsman_record(batsman, df):
    if df.empty:
        return np.nan
    out = df[df['player_out'] == batsman].shape[0]
    df = df[df['batter'] == batsman]
    fours = df[df['batsman_run'] == 4].shape[0]
    sixes = df[df['batsman_run'] == 6].shape[0]
    innings = df['ID'].unique().shape[0]
    runs = df['batsman_run'].sum()
    if out:
        avg = runs / out
    else:
        avg = np.inf
    no_balls = df[~(df['extra_type'] == 'wides')].shape[0]
    if no_balls:
        strike_rate = runs / no_balls * 100
    else:
        strike_rate = 0
    gb = df.groupby('ID').sum()
    fifties = gb[(gb['batsman_run'] >= 50) & (gb['batsman_run'] < 100)].shape[0]
    hundreds = gb[gb['batsman_run'] >= 100].shape[0]
    mom = df[df['Player_of_Match'] == batsman].drop_duplicates('ID', keep='first').shape[0]
    not_out = innings - out
    return {
        'innings': innings,
        'runs': runs,
        'fours': fours,
        'sixes': sixes,
        'avg': float(avg),
        'strikeRate': float(strike_rate),
        'fifties': fifties,
        'hundreds': hundreds,
        'notOut': not_out,
        'mom': mom,
        'number of balls': no_balls
    }

def batsmanVsTeam(batsman, team, df):
    df = df[df.BowlingTeam == team].copy()
    return batsman_record(batsman, df)

def batsmanAPI(batsman, balls=batter_data):
    df = balls[balls.innings.isin([1, 2])]
    self_record = batsman_record(batsman, df=df)
    TEAMS = matches.Team1.unique()
    against = {team: batsmanVsTeam(batsman, team, df) for team in TEAMS}
    data = {
        batsman: {'all': self_record, 'against': against}
    }
    return json.dumps(data, cls=NpEncoder)

def bowlerwicket(a):
    if a.iloc[0] in ['caught', 'caught and bowled', 'bowled', 'stumped', 'lbw', 'hit wicket']:
        return a.iloc[1]
    else:
        return 0

batter_data['isBowlerWicket'] = batter_data[['kind', 'isWicketDelivery']].apply(bowlerwicket, axis=1)

def bowlerrun(b):
    if b.iloc[0] in ['penalty', 'legbyes', 'byes']:
        return 0
    else:
        return b.iloc[1]

batter_data['bowler_run'] = batter_data[['extra_type', 'total_run']].apply(bowlerrun, axis=1)

def bowlerRecord(bowler, df):
    df = df[df['bowler'] == bowler]
    inngs_total = df.ID.unique().shape[0]
    runs = df['bowler_run'].sum()
    nballs = df[~(df.extra_type.isin(['wides', 'noballs']))].shape[0]
    if nballs:
        eco = runs / nballs * 6
    else:
        eco = 0
    fours = df[(df.batsman_run == 4) & (df.non_boundary == 0)].shape[0]
    sixes = df[(df.batsman_run == 6) & (df.non_boundary == 0)].shape[0]
    wicket = df.isBowlerWicket.sum()
    if wicket:
        avg = runs / wicket
    else:
        avg = np.inf
    if wicket:
        strike_rate = nballs / wicket * 100
    else:
        strike_rate = np.nan
    gb = df.groupby('ID').sum()
    w_3 = gb[(gb.isBowlerWicket >= 3)].shape[0]
    best_wicket = gb.sort_values(['isBowlerWicket', 'bowler_run'], ascending=[False, True])[
        ['isBowlerWicket', 'bowler_run']].head(1).values
    if best_wicket.size > 0:
        best_figure = f'{best_wicket[0][0]}/{best_wicket[0][1]}'
    else:
        best_figure = np.nan
    mom = df[df.Player_of_Match == bowler].drop_duplicates('ID', keep='first').shape[0]
    data = {
        'innings': inngs_total,
        'wicket': wicket,
        'economy': eco,
        'average': avg,
        'avg': avg,
        'strikeRate': strike_rate,
        'fours': fours,
        'sixes': sixes,
        'best_figure': best_figure,
        '3+W': w_3,
        'mom': mom
    }
    return data

def bowlerVsTeam(bowler, team, df):
    df = df[df.BattingTeam == team].copy()
    return bowlerRecord(bowler, df)

def bowlerAPI(bowler, balls=batter_data):
    df = balls[balls.innings.isin([1, 2])]
    self_record = bowlerRecord(bowler, df=df)
    TEAMS = matches.Team1.unique()
    against = {team: bowlerVsTeam(bowler, team, df) for team in TEAMS}
    data = {
        bowler: {'all': self_record, 'against': against}
    }
    return json.dumps(data, cls=NpEncoder)
