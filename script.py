from flask import Flask, render_template, request, jsonify
import requests
import random
from api import api
import sqlite3 as sl

con = sl.connect('my-test.db')

app = Flask(__name__)
app.register_blueprint(api)

@app.route('/')
def poke():
    page = request.args.get('page')
    page = int(page) if page and page.isdigit() else 1
    search_string = request.args.get('search_string', '').strip()
    response = requests.get(f'{request.host_url}/api/v1/pokemon/list?page={page}&search_string={search_string}')
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
    response = requests.get(f'{request.host_url}/api/v1/pokemon/{name}')
    if response.status_code == 200:
        return render_template('pokemon.html', poke=response.json())
    else:
        return "Pokemon not found", 404
    
# @app.route('/battle/<name>')
# def battle(name):
#     chosen_pokemon_info = get_pokemon_info(name)
#     random_pokemon_info = get_random_pokemon()
#     return render_template('battle.html', chosen_pokemon=chosen_pokemon_info, random_pokemon=random_pokemon_info)

@app.route('/battle/<int:user_input>')
def fight(user_input):
    opponent_number = random.randint(1, 10)
    result = ""
    if user_input % 2 == opponent_number % 2:
        result = "Ваш покемон атакован!"
    else:
        result = "Покемон противника атакован!"
    return jsonify({'result': result})


if __name__ == '__main__':
    app.run(debug=True)