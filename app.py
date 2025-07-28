from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def get_pokedata(pokemon):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()

def get_type_color(pokemon_type):
    """Retorna el color hexadecimal basado en el tipo del Pokémon"""
    type_colors = {
        'normal': '#A8A878',
        'fire': '#F08030',
        'water': '#6890F0',
        'electric': '#F8D030',
        'grass': '#78C850',
        'ice': '#98D8D8',
        'fighting': '#C03028',
        'poison': '#A040A0',
        'ground': '#E0C068',
        'flying': '#A890F0',
        'psychic': '#F85888',
        'bug': '#A8B820',
        'rock': '#B8A038',
        'ghost': '#705898',
        'dragon': '#7038F8',
        'dark': '#705848',
        'steel': '#B8B8D0',
        'fairy': '#EE99AC'
    }
    return type_colors.get(pokemon_type, '#68A090')  # Color por defecto

def get_pokeinfo(index, data):
    name = data["name"].capitalize()
    abilities = [a["ability"]["name"] for a in data["abilities"]]
    height = data["height"]
    weight = data["weight"]
    types = [t["type"]["name"] for t in data["types"]]
    
    # Obtener el color del tipo principal (primer tipo)
    primary_type = types[0] if types else 'normal'
    type_color = get_type_color(primary_type)
    
    # Crear diccionario con la información del Pokémon
    pokemon_info = {
        'index': index,
        'name': name,
        'abilities': abilities,
        'height': height,
        'weight': weight,
        'types': types,
        'primary_type': primary_type,
        'type_color': type_color,
        'sprite': data.get('sprites', {}).get('front_default', '')
    }
    
    return pokemon_info

def one_pokemon(pokemon):
    data = get_pokedata(pokemon)
    if data:
        index = data["id"]
        return get_pokeinfo(index, data)
    else:
        return "No se pudo obtener info del pokemon"

# Una mousequeherramienta q la usare mas adelante

#Q monda es eso?
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
