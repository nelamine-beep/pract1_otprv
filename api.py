from flask import Blueprint, make_response, request

import requests, random

api = Blueprint('api', __name__, template_folder='templates')

@api.route('/api/v1/pokemon/<id>', methods=['GET'])
def api_pokemon_from_id(id):
    if id:
        url = f"https://pokeapi.co/api/v2/pokemon/{id}/"
        response = requests.get(url)
        if (response.status_code == 200):
            data = response.json()
            name = data['name']
            pokemon_info = requests.get(url).json()
            health = pokemon_info['stats'][0]['base_stat']
            attack = pokemon_info['stats'][1]['base_stat']
            species = pokemon_info['species']['name']
            species_url = pokemon_info['species']['url']
            species_data = requests.get(species_url).json()
            gender_rate = species_data['gender_rate']
            gender = "Male" if gender_rate == 0 else "Female" if gender_rate == 8 else "Both"
            color = species_data['color']['name']
            image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{data['id']}.png"
            result = {
                            'id': data['id'],
                            'name': name, 
                            'image_url': image_url, 
                            'health': health, 
                            'attack': attack, 
                            'species': species, 
                            'gender': gender, 
                            'color': color}
            return make_response(result, 200)
        else:
            return make_response({'error': 'Not Found'}, 404)
    return make_response({'error': 'Not Found'}, 404)


@api.route('/api/v1/pokemon/random', methods=['GET'])
def api_pokemon_random():
    url = f"https://pokeapi.co/api/v2/pokemon/?limit=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        poke_count = data['count']
        random_id = random.randint(1, poke_count)
        return make_response({'id': random_id}, 200)
    else:
        return make_response({'error': 'Not Found'}, 404)

@api.route('/api/v1/pokemon/list', methods=['GET'])
def api_pokemon_list():
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    search_string = request.args.get('search_string', '').strip()

    offset = (page - 1) * limit
    url = f"https://pokeapi.co/api/v2/pokemon?offset={offset}&limit={limit}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        poke_list = data.get('results', [])
        poke_count = data['count']
        page_count = (poke_count + limit - 1) // limit

        if search_string != '':
            url = f"https://pokeapi.co/api/v2/pokemon?limit={poke_count}"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                poke_list = data.get('results', [])
                poke_list = [pkm for pkm in poke_list if search_string in pkm['name']]
                page_count = (len(poke_list) + limit - 1) // limit
                poke_list = poke_list[offset:offset + limit]
            else:
                return make_response({'error': 'Not Found'}, 404)

        poke_list_data = []

        for pkm in poke_list:
            pkm_name = pkm['name']
            pkm_data = api_pokemon_from_id(pkm_name).json
            poke_list_data.append(pkm_data)
        return make_response({'page_count': page_count, 'list': poke_list_data}, 200)
    else:
        return make_response({'error': 'Not Found'}, 404)