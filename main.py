from flask import Flask,jsonify,request
import ipl


app = Flask(__name__)

@app.route('/')
def home():
    seasons=ipl.season()
    return jsonify(seasons)

@app.route('/api/teams')
def teams():
    teams = ipl.teamsApi()
    return jsonify(teams)

@app.route('/api/teamvteam')
def teamvteam():
    team1 = request.args.get('team1')
    team2 = request.args.get('team2')

    response = ipl.team_vs_team(team1,team2)
    print(response)
    return jsonify(response)

@app.route('/api/team-record')
def team_record():
    team_name = request.args.get('team')
    response = ipl.allRecord(team_name)
    return response

@app.route('/api/batting-record')
def batting_record():
    batsman_name = request.args.get('batsman')
    response = ipl.batsmanAPI(batsman_name)
    return response

@app.route('/api/bowling-record')
def bowling_record():
    bowler_name = request.args.get('bowler')
    response = ipl.bowlerAPI(bowler_name)
    return response


app.run(debug=True)