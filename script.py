from flask import Flask, render_template, redirect, url_for, request
import requests

app = Flask(__name__)

def get_pokemon_list(url, limit=10, offset=0):
	base_url = url
	params = {"limit": limit, "offset": offset}

	response = requests.get(base_url, params=params)

	if response.status_code == 200:
		data = response.json()
		return data["results"]
	else:
		print("Не удалось получить список покемонов")
		return []


url = 'https://pokeapi.co/api/v2/pokemon'
res = requests.get(url)
data = res.json()
limit = data["count"]
offset = 0

pokemon_list = get_pokemon_list(url, limit, offset)
name_list = []
if pokemon_list:
	# print("Список покемонов:")
	for index, pokemon in enumerate(pokemon_list, start=offset + 1):
		# print(f"{index}. {pokemon['name']}")
		name_list.append(pokemon['name'])

pokemon_name = ''
@app.route("/search", methods=["POST"])
def search():
	pokemon_name = request.form["search_string"]
	if pokemon_name == "":
		return redirect(url_for("index"))
	else:
		url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}/"
		response = requests.get(url)

		if response.status_code == 200:
			data = response.json()
			result = {
				data["name"]
			}
			return render_template("index.html", name_list=result, search_string=pokemon_name)
		else:
			return render_template("index.html", name_list=[], search_string=pokemon_name)


@app.route('/')
def index():
    return render_template('index.html', name_list = name_list, search_string = pokemon_name)

if __name__ == '__main__':
    app.run()
