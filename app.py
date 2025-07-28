from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def get_pokedata(pokemon):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()

def get_pokeinfo(index, data):
    name = data["name"].capitalize()
    abilities = [a["ability"]["name"] for a in data["abilities"]]
    height = data["height"]
    weight = data["weight"]
    types = [t["type"]["name"] for t in data["types"]]

    info = f"Numero en la pokedex No. {index}, Nombre: {name} \
     \nnombre: {name} \
     \nhabilidades: {', '.join(abilities)} \
     \naltura: {height} \
     \npeso: {weight} \
     \nTipos: {', '.join(types)}"

    return info

def one_pokemon(pokemon):
    data = get_pokedata(pokemon)
    if data:
        index = data["id"]
        return get_pokeinfo(index, data)
    else:
        return "No se pudo obtener info del pokemon"

# Una mousequeherramienta q la usare mas adelante
def n_pokemons():
    n = input("ingresa el numero de pokemons que quieres ver: ")
    try:
        limit = int(n)
        if limit <= 0:
            print("Numero invalido")
            return
    except ValueError:
        print("Numero invalido")
        return
    print(f"Obteniendo información de {limit} Pokémon(s)...")
    for i in range(1, limit + 1):
        data = get_pokedata(i)
        if data:
            get_pokeinfo(i, data)
    else:
        print("No se pudo obtener la información del Pokémon. Verifica el nombre o número ingresado.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pokedex', methods=['GET', 'POST'])
def pokedex():
    if request.method == 'POST':
        valor = request.form.get('valor')
    elif request.method == 'GET':
        valor = request.args.get('valor')
    info = one_pokemon(valor) if valor else ""
    return render_template('pokedex.html',
                           datos=info)

if __name__ == '__main__':
    app.run()
