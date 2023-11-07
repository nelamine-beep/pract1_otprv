from flask import Flask, render_template, request, jsonify
import requests
import random
import sqlite3 as sl

con = sl.connect('my-test.db')


app = Flask(__name__)

# Получите список всех покемонов из API
def get_pokemons(offset, limit=10, methods=['GET']):
    pokemon_data = []

    url = f"https://pokeapi.co/api/v2/pokemon?offset={offset}&limit={limit}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        for pokemon in data['results']:
            name = pokemon['name']
            pokemon_url = pokemon['url']
            pokemon_info = requests.get(pokemon_url).json()
            health = pokemon_info['stats'][0]['base_stat']
            attack = pokemon_info['stats'][1]['base_stat']
            image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_url.split('/')[-2]}.png"
            pokemon_data.append({'name': name, 'image_url': image_url, 'health': health, 'attack': attack})

    return pokemon_data

def get_pokemons_by_name(name):
    pokemon_data = []

    url = f"https://pokeapi.co/api/v2/pokemon/{name}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        name = data['name']
        health = data['stats'][0]['base_stat']
        attack = data['stats'][1]['base_stat']
        image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{data['id']}.png"
        pokemon_data.append({'name': name, 'image_url': image_url, 'health': health, 'attack': attack})

    return pokemon_data

@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    search_term = request.args.get('search')

    if search_term:
        search_term = search_term.lower()
        pokemon_data = get_pokemons_by_name(search_term)
    else:
        offset = (page - 1) * limit
        pokemon_data = get_pokemons(offset, limit)

    return render_template('index.html', pokemon_data=pokemon_data, page=page, limit=limit)

@app.route('/pokemon/<name>')
def pokemon(name):
    url = f"https://pokeapi.co/api/v2/pokemon/{name}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        name = data['name']
        image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{data['id']}.png"
        health = data['stats'][0]['base_stat']
        attack = data['stats'][1]['base_stat']
        species = data['species']['name']

        species_url = data['species']['url']
        species_data = requests.get(species_url).json()
        gender_rate = species_data['gender_rate']
        gender = "Male" if gender_rate == 0 else "Female" if gender_rate == 8 else "Both"

        color = species_data['color']['name']

        return render_template('pokemon.html', name=name, image_url=image_url, health=health, attack=attack, species=species, gender=gender, color=color)
    else:
        return "Pokemon not found", 404

def get_random_pokemon():
    random_id = random.randint(1, 1000)
    url = f"https://pokeapi.co/api/v2/pokemon/{random_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        name = data['name']
        image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{random_id}.png"
        health = data['stats'][0]['base_stat']
        attack = data['stats'][1]['base_stat']
        return {'name': name, 'image_url': image_url, 'health': health, 'attack': attack}
    else:
        return None
    
def get_pokemon_info(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        name = data['name']
        image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{data['id']}.png"
        health = data['stats'][0]['base_stat']
        attack = data['stats'][1]['base_stat']
        return {'name': name, 'image_url': image_url, 'health': health, 'attack': attack}
    else:
        return None
    
@app.route('/battle/<name>')
def battle(name):
    chosen_pokemon_info = get_pokemon_info(name)
    random_pokemon_info = get_random_pokemon()
    return render_template('battle.html', chosen_pokemon=chosen_pokemon_info, random_pokemon=random_pokemon_info)

@app.route('/battle/<int:user_input>')
def fight(user_input):
    opponent_number = random.randint(1, 10)
    result = ""
    if user_input % 2 == opponent_number % 2:
        result = "Ваш покемон атакован!"
    else:
        result = "Покемон противника атакован!"
    return jsonify({'result': result})


@app.route('/pokemon/list', methods=['GET'])
def get_pokemon_list():
    filters = request.args  # Получите параметры фильтрации из запроса
    pokemon_list = get_pokemons_by_name(filters)  # Реализуйте функцию для фильтрации данных
    return jsonify(pokemon_list)


if __name__ == '__main__':
    app.run(debug=True)