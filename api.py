from flask import Blueprint, make_response, request
import json, requests, random, io, ftplib
from datetime import date

api = Blueprint('api', __name__, template_folder='templates')

with open('config.json', 'r') as file:
    data=file.read()
    configs = json.loads(data)


@api.route('/api/v2/pokemon/<id>', methods=['GET'])
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
            image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/dream-world/{data['id']}.svg"
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


@api.route('/api/v2/pokemon/random', methods=['GET'])
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

@api.route('/api/v2/pokemon/list', methods=['GET'])
def api_pokemon_list():
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=10, type=int)
    search_string = request.args.get('search_string', '').strip()
    offset = (page - 1) * limit

    # Получите общее количество покемонов (без учета фильтра по имени)
    url = "https://pokeapi.co/api/v2/pokemon/"
    total_pokemon_response = requests.get(url)
    if total_pokemon_response.status_code != 200:
        return make_response({'error': 'Not Found'}, 404)
    total_pokemon_data = total_pokemon_response.json()
    total_pokemon_count = total_pokemon_data['count']

    # Фильтрация по имени, если задан поисковый запрос
    if search_string:
        url = f"https://pokeapi.co/api/v2/pokemon/?limit={total_pokemon_count}"
        response = requests.get(url)
        if response.status_code != 200:
            return make_response({'error': 'Not Found'}, 404)
        data = response.json()
        poke_list = [pkm for pkm in data.get('results', []) if search_string in pkm['name']]
    else:
        url = f"https://pokeapi.co/api/v2/pokemon?offset={offset}&limit={limit}"
        response = requests.get(url)
        if response.status_code != 200:
            return make_response({'error': 'Not Found'}, 404)
        data = response.json()
        poke_list = data.get('results', [])

    # Вычисление общего количества страниц
    page_count = (total_pokemon_count + limit - 1) // limit

    # Формирование данных для отображения
    poke_list_data = []
    for pkm in poke_list:
        pkm_name = pkm['name']
        pkm_data = api_pokemon_from_id(pkm_name).json
        poke_list_data.append(pkm_data)

    return make_response({'page_count': page_count, 'list': poke_list_data}, 200)

@api.route('/api/v1/fight', methods=['GET'])
def api_fight():
    select_poke_id = request.args.get('select_poke_id')
    opponent_poke_id = request.args.get('opponent_poke_id')
    if select_poke_id and select_poke_id.isdigit() and opponent_poke_id and opponent_poke_id.isdigit():
        select_poke_info = api_pokemon_from_id(select_poke_id).json if api_pokemon_from_id(select_poke_id).status_code == 200 else None
        opponent_poke_info = api_pokemon_from_id(opponent_poke_id).json if api_pokemon_from_id(opponent_poke_id).status_code == 200 else None
        
        if select_poke_info and opponent_poke_info:
            result = {
                'select_poke': select_poke_info,
                'opponent_poke': opponent_poke_info,
            }
            return make_response(result, 200)
        else:
            return make_response({'error': 'Not Found'}, 404)
    else:
        return make_response({'error': 'Bad Request'}, 400)
    
@api.route('/api/v1/fight/<int:select_number>', methods=['POST'])
def api_fight_round(select_number):
    select_poke = request.json['select_poke']
    opponent_poke = request.json['opponent_poke']
    if select_poke and opponent_poke and select_number > 0 and select_number < 11:
        if {'id', 'health', 'attack'}.issubset(set(select_poke)) and {'id', 'health', 'attack'}.issubset(set(opponent_poke)):
            select_poke_hp = select_poke['health']
            opponent_poke_hp = opponent_poke['health']
            round_winner_id = None
            
            # get random number opponent
            opponent_number = random.randint(1, 10)
            # attack logic
            if select_poke_hp > 0 and opponent_poke_hp > 0:
                if select_number % 2 == opponent_number % 2:
                    opponent_poke_hp -= select_poke['attack']
                    round_winner_id = select_poke['id']
                else:
                    select_poke_hp -= opponent_poke['attack']
                    round_winner_id = opponent_poke['id']
            winner = None
            if select_poke_hp <= 0:
                winner = opponent_poke['id']
            elif opponent_poke_hp <= 0:
                winner = select_poke['id']
            # result round
            result = {
                'select_poke': {
                    'id': select_poke['id'],
                    'health': select_poke_hp,
                    'attack': select_poke['attack'],
                },
                'opponent_poke': {
                    'id': opponent_poke['id'],
                    'health': opponent_poke_hp,
                    'attack': opponent_poke['attack'],
                },
                'round': {
                    'winner_id': round_winner_id,
                    'select_number': select_number,
                    'opponent_number': opponent_number,
                    'select_poke_hp': select_poke_hp,
                    'opponent_poke_hp': opponent_poke_hp,
                },
                'winner': winner,
            }
            return make_response(result, 200)  
    return make_response({'error': 'Bad Request'}, 400)
    

@api.route('/api/v1/fight/fast', methods=['GET'])
def api_fight_fast():
    select_poke_id = request.args.get('select_poke_id')
    opponent_poke_id = request.args.get('opponent_poke_id')
    if select_poke_id and select_poke_id.isdigit() and opponent_poke_id and opponent_poke_id.isdigit():
        select_poke_info = api_pokemon_from_id(select_poke_id).json if api_pokemon_from_id(select_poke_id).status_code == 200 else None
        opponent_poke_info = api_pokemon_from_id(opponent_poke_id).json if api_pokemon_from_id(opponent_poke_id).status_code == 200 else None

        if select_poke_info and opponent_poke_info:
            select_poke_hp = select_poke_info['health']
            opponent_poke_hp = opponent_poke_info['health']
            rounds = []
            while select_poke_hp > 0 and opponent_poke_hp > 0:
                select_number = random.randint(1, 10)
                url = f'{request.host_url}/api/v1/fight/{select_number}'
                response = requests.post(url, json={
                    'select_poke': {
                        'id': select_poke_info['id'],
                        'health': select_poke_hp,
                        'attack': select_poke_info['attack'],
                    },
                    'opponent_poke': {
                        'id': opponent_poke_info['id'],
                        'health': opponent_poke_hp,
                        'attack': opponent_poke_info['attack'],
                    },
                })

                if response.status_code == 200:
                    select_poke_hp = response.json()['select_poke']['health']
                    opponent_poke_hp = response.json()['opponent_poke']['health']
                    winner = response.json()['winner']
                    rounds.append(response.json()['round'])
                else:
                    return make_response({'error': 'Service Unavailable'}, 503)

                if winner:
                    break

            result = {
                'select_poke': {
                    'id': select_poke_info['id'],
                    'health': select_poke_hp,
                    'attack': select_poke_info['attack'],
                },
                'opponent_poke': {
                    'id': opponent_poke_info['id'],
                    'health': opponent_poke_hp,
                    'attack': opponent_poke_info['attack'],
                },
                'rounds': rounds,
                'winner': winner,
            }
            return make_response(result, 200)  
        else:
            return make_response({'error': 'Not Found'}, 404)
    else:
        return make_response({'error': 'Bad Request'}, 400)
    

@api.route('/api/v1/pokemon/save/<int:id>', methods=['POST'])
def api_pokemon_save_from_id(id):
    poke_info = api_pokemon_from_id(id).json if api_pokemon_from_id(id).status_code == 200 else None
    if poke_info:
        folder_name = str(date.today()).replace('-', '').strip()
        text_markdown = f"# {poke_info['name']}\n\n### Poke Information:\n- hp: {poke_info['health']}\n- attack: {poke_info['attack']}\n"
        byte_text_markdown = text_markdown.encode('utf-8')

        try:
            ftp = ftplib.FTP(host=configs['FTP_HOST'])
            ftp.login(user=configs['FTP_USER'], passwd=configs['FTP_PASSWORD'])

            files = ftp.nlst()
            if folder_name not in files:
                ftp.mkd(folder_name)
            ftp.cwd(folder_name)
            ftp.storbinary(f"STOR {poke_info['name']}.md", io.BytesIO(byte_text_markdown))
            return make_response({'result': 'file was successfully generated and saved',
                                  'poke_name': poke_info['name']}, 201) 
        except:
            return make_response({'error': 'Service Unavailable',
                                  'poke_name': poke_info['name']}, 503)
        finally:
            ftp.quit()
    return make_response({'error': 'Bad Request'}, 400)