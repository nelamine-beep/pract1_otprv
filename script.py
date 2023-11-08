from flask import Flask, render_template, request, redirect, url_for, session, abort
import requests
import random
from send_email import *
from api import api
import sqlite3 as sl
from db import *
import re
import logging


app = Flask(__name__)
app.register_blueprint(api)
app.logger.setLevel(logging.ERROR)
app.config['SQLALCHEMY_DATABASE_URI'] = connect_string
db.init_app(app)
with open('config.json', 'r') as file:
    data=file.read()
configs = json.loads(data)
app.config['SECRET_KEY'] = configs['SECRET_KEY']

@app.route('/')
def pokemon():
    page = request.args.get('page')
    page = int(page) if page and page.isdigit() else 1
    search_string = request.args.get('search_string', '').strip()
    response = requests.get(f'{request.host_url}/api/v2/pokemon/list?page={page}&search_string={search_string}')
    if response.status_code == 200:
        return render_template('index.html', 
                                pokemons=response.json()['list'], 
                                search_string=search_string,
                                page=page, 
                                end=response.json()['page_count'])
    else:
        return render_template('index.html', 
                                pokemons=[],
                                search_string='',
                                page=0,
                                end=0)

@app.route('/pokemon/<string:name>')
def pokemon_page(name):
    response = requests.get(f'{request.host_url}/api/v2/pokemon/{name}')
    if response.status_code == 200:
        return render_template('pokemon.html', poke=response.json())
    else:
        return "Pokemon not found", 404
    
@app.route('/battle', methods=['GET', 'POST'])
def battle():
    if request.method == 'POST' and 'select_poke_id' in request.form:
        select_poke_id = request.form['select_poke_id']
        # clear old data about battle 
        session.clear()
        print('select_poke_id', select_poke_id)
        # get randow opponent poke & info about select and opponent poke
        response = requests.get(f'{request.host_url}/api/v2/pokemon/random')
        if response.status_code == 200:
            opponent_poke_id = response.json()['id']
            print('opponent_poke_id', opponent_poke_id)
            response = requests.get(f'{request.host_url}/api/v1/fight?select_poke_id={select_poke_id}&opponent_poke_id={opponent_poke_id}')
            if response.status_code == 200:
                select_poke_info = response.json()['select_poke']
                opponent_poke_info = response.json()['opponent_poke']
                # save info
                session['select_poke_id'] = select_poke_info['id']
                session['select_poke_health'] = select_poke_info['health']
                session['select_poke_attack'] = select_poke_info['attack']
                session['opponent_poke_id'] = opponent_poke_info['id']
                session['opponent_poke_health'] = opponent_poke_info['health']
                session['opponent_poke_attack'] = opponent_poke_info['attack']
                return render_template('battle.html',
                               select_poke=select_poke_info,
                               opponent_poke=opponent_poke_info)
    return redirect(url_for('pokemon'))
@app.route('/battle/round', methods=['GET', 'POST'])
def battle_round():
    if request.method == 'POST' and 'select_number' in request.form:
        select_number = request.form['select_number']
        # someone has already won, there are no more rounds
        if session['select_poke_health'] <= 0 or session['opponent_poke_health'] <= 0:
            return redirect(url_for('pokemon'))
        # get info about select & opponent poke
        response = requests.get(f'{request.host_url}/api/v1/fight?select_poke_id={session["select_poke_id"]}&opponent_poke_id={session["opponent_poke_id"]}')
        if response.status_code == 200:
            select_poke_info = response.json()['select_poke']
            opponent_poke_info = response.json()['opponent_poke']
        else:
            abort(503)
        # checking valid selected number (from user)
        if select_number.isdigit() and int(select_number) > 0 and int(select_number) < 11:
            # next step & get new info about battle
            url = f'{request.host_url}/api/v1/fight/{select_number}'
            response = requests.post(url, json={
                'select_poke': {
                    'id': session['select_poke_id'],
                    'health': session['select_poke_health'],
                    'attack': session['select_poke_attack'],
                },
                'opponent_poke': {
                    'id': session['opponent_poke_id'],
                    'health': session['opponent_poke_health'],
                    'attack': session['opponent_poke_attack'],
                },
            })
            
            if response.status_code == 200:
                session['select_poke_health'] = response.json()['select_poke']['health']
                session['opponent_poke_health'] = response.json()['opponent_poke']['health']
                winner = response.json()['winner']
                # add info about round to history
                if 'history' not in session:
                    session['history'] = []
                session['history'].append(response.json()['round'])
                # check if the battle is over 
                if winner:
                    try:
                        battle = BattleResult(user_id=session['select_poke_id'],
                                        opponent_id=session['opponent_poke_id'],
                                        winner_id=winner,
                                        rounds=len(session['history']))
                        db.session.add(battle)
                        db.session.commit()
                    except Exception:
                        print("ERROR DB: Battle failed to add")
                        db.session.rollback()
                print(winner)
                
                return render_template('battle.html',
                            select_poke=select_poke_info, 
                            opponent_poke=opponent_poke_info,
                            rounds_result=session['history'],
                            winner=winner)
            else:
                abort(503)
        else:
            return render_template('battle.html',
                                    select_poke=select_poke_info, 
                                    opponent_poke=opponent_poke_info)
    return redirect(url_for('pokemon'))
def is_valid_email(email):
    regex = r'\b[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    return True if re.fullmatch(regex, email) else False


def results_battle_to_string(select_poke, opponent_poke, rounds, winner):
    res = f'\nBATTLE {select_poke["name"]} VS {opponent_poke["name"]}\nRESULT: {select_poke["name"] if winner == select_poke["id"] else opponent_poke["name"]} wins.\n\nROUNDS:'
    for i, round in enumerate(rounds):
        round_winner = select_poke["name"] if round['winner_id'] == select_poke["id"] else opponent_poke["name"]
        res += f'\n\n#{i+1}: WIN {round_winner}\nY-N={round["select_number"]}   Y-HP={round["select_poke_hp"]}   O-N={round["opponent_number"]}   O-HP={round["opponent_poke_hp"]}'
    return res + '\n\n'


@app.route('/battle/fast', methods=['GET', 'POST'])
def fast_battle():
    if request.method == 'POST':
        if 'select_poke_id' in session and 'opponent_poke_id' in session:
            # someone has already won, there are no more rounds
            if session['select_poke_health'] <= 0 or session['opponent_poke_health'] <= 0:
                return redirect(url_for('pokemon'))
            # get info about select & opponent poke
            response = requests.get(f'{request.host_url}/api/v1/fight?select_poke_id={session["select_poke_id"]}&opponent_poke_id={session["opponent_poke_id"]}')
            if response.status_code == 200:
                select_poke_info = response.json()['select_poke']
                opponent_poke_info = response.json()['opponent_poke']
            else:
                abort(503)
            # get result of the battle (fast)
            response = requests.get(f'{request.host_url}/api/v1/fight/fast?select_poke_id={session["select_poke_id"]}&opponent_poke_id={session["opponent_poke_id"]}')
            if response.status_code == 200:
                session['select_poke_health'] = response.json()['select_poke']['health']
                session['opponent_poke_health'] = response.json()['opponent_poke']['health']
                rounds = response.json()['rounds']
                winner = response.json()['winner']
                
                # record result of the battle to db
                try:
                    battle = BattleResult(user_id=session['select_poke_id'],
                                        opponent_id=session['opponent_poke_id'],
                                        winner_id=winner,
                                        rounds=len(rounds))
                    db.session.add(battle)
                    db.session.commit()
                except Exception as e:
                    app.logger.error(f"Ошибка при добавлении записи в базу данных: {str(e)}")
                    db.session.rollback()
                
                battle_result = results_battle_to_string(select_poke=select_poke_info,
                                                        opponent_poke=opponent_poke_info,
                                                        rounds=rounds,
                                                        winner=winner)
                send_email(to_email=to_email, subject=subject,
                               message=battle_result.replace('\n', '       '))
                return render_template('battle.html',
                            select_poke=select_poke_info, 
                            opponent_poke=opponent_poke_info,
                            rounds_result=rounds,
                            winner=winner)
            else:
                abort(503)
    return redirect(url_for('pokemon'))
# @app.route('/result-battes')
# def result_battes():
#     try:
#         all_battles = BattleResult.query.order_by(BattleResult.created_at.desc()).all()
#         return render_template('results.html',
#                                 battles=all_battles)
#     except:
#         abort(503)

if __name__ == '__main__':
    app.run(debug=True)