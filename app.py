from flask import Flask, render_template, request
import requests

app = Flask(__name__)

REGIONES = {
    'kanto': 'generation-i',
    'johto': 'generation-ii',
    'hoenn': 'generation-iii',
    'sinnoh': 'generation-iv',
    'teselia': 'generation-v',
    'kalos': 'generation-vi',
    'alola': 'generation-vii',
    'galar': 'generation-viii',
    'paldea': 'generation-ix'
}

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
    return type_colors.get(pokemon_type, '#68A090')  # por si no lo encuentra, devuelve un color por defecto, que no es normal, porque normal es un tipo, entonces no se puede usar como color por defecto, capicci?

def get_pokeinfo(index, data):
    name = data["name"].capitalize()
    abilities = [a["ability"]["name"] for a in data["abilities"]]
    height = data["height"]
    weight = data["weight"]
    types = [t["type"]["name"] for t in data["types"]]
    
    # Obtener el color del tipo principal (primer tipo) para usarlo en el CSS
    primary_type = types[0] if types else 'normal'
    type_color = get_type_color(primary_type)
    
    # Puedes creer que tuve que ir a mirar un tutorial, porque se me olvido como se hacia esto? XD
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
        return None

def get_region(region):
    url = f"https://pokeapi.co/api/v2/generation/{region}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_region_info(region):
    region = REGIONES.get(region.lower())
    if not region:
        return None

    data = get_region(region)
    if not data:
        return None

    species = [p['name'] for p in data["pokemon_species"]]
    pokemons = []
    # Optimizamos esta madre para manejar mejor las peticiones
    for species_name in species:
        try:
            pokedata = get_pokedata(species_name)
            if pokedata:
                info = get_pokeinfo(pokedata["id"], pokedata)
                pokemons.append(info)
        except:
            continue

    return sorted(pokemons, key=lambda x: x['index']) if pokemons else None

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
    # Listo ya no esta tan feo
    if not valor:
        return render_template('pokedex.html')

    info = one_pokemon(valor)
    if info is None:
        region = get_region_info(valor)
        return render_template('pokedex.html',
                               es_region=True,
                               pokemons=region)

    return render_template('pokedex.html',
                            es_region=False,
                            datos=info)

if __name__ == '__main__':
    app.run()
