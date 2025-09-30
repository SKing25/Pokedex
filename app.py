from flask import Flask, redirect, render_template, request, jsonify
import requests
import random
import os
from openai import OpenAI
from collections import OrderedDict

app = Flask(__name__)

# Configuración del cliente de OpenAI para "IvAn"
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

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

# ---- OPTIMIZACIÓN: CACHE LRU ----
class LRUCache:
    def __init__(self, max_size):
        self.max_size = max_size
        self.cache = OrderedDict()
    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

# Configuración para Render (RAM muy limitada)
if os.getenv('RENDER'):
    MAX_POKEMON_CACHE = 10
    MAX_TYPE_CACHE = 5
    MAX_ABILITY_CACHE = 5
    MAX_SPRITES_CACHE = 5
else:
    MAX_POKEMON_CACHE = 30
    MAX_TYPE_CACHE = 10
    MAX_ABILITY_CACHE = 10
    MAX_SPRITES_CACHE = 10

POKEMON_CACHE = LRUCache(MAX_POKEMON_CACHE)
TYPE_RELATIONS_CACHE = LRUCache(MAX_TYPE_CACHE)
ABILITY_CACHE = LRUCache(MAX_ABILITY_CACHE)
REGION_CACHE = LRUCache(10)
SPRITES_CACHE = LRUCache(MAX_SPRITES_CACHE)

# ---- FUNCIONES OPTIMIZADAS ----
def get_pokedata(pokemon):
    key = str(pokemon).lower()
    cached = POKEMON_CACHE.get(key)
    if cached:
        return cached
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            essential_data = {
                'id': data['id'],
                'name': data['name'],
                'types': data['types'],
                'abilities': data['abilities'],
                'stats': data['stats'],
                'height': data['height'],
                'weight': data['weight'],
                'sprite': data['sprites'].get('front_default')
            }
            POKEMON_CACHE.set(key, essential_data)
            return essential_data
    except Exception as e:
        print(f"Error fetching Pokemon {pokemon}: {e}")
    return None

def get_type_color(pokemon_type):
    type_colors = {
        'normal': '#A8A878',
        'fire': '#F08030',
        'water': '#6890F0',
        'electric': '#F8D030',
        'grass': '#78C850',
        'ice': "#008F8F",
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
    return type_colors.get(pokemon_type, '#68A090')

def get_damage_relations(pokemon_types):
    all_resistances = {}
    all_weaknesses = {}
    for pokemon_type in pokemon_types:
        cached = TYPE_RELATIONS_CACHE.get(pokemon_type)
        if cached:
            for k, v in cached['all_resistances'].items():
                if k in all_resistances:
                    all_resistances[k] *= v
                else:
                    all_resistances[k] = v
            for k, v in cached['all_weaknesses'].items():
                if k in all_weaknesses:
                    all_weaknesses[k] *= v
                else:
                    all_weaknesses[k] = v
            continue
        url = f"https://pokeapi.co/api/v2/type/{pokemon_type}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for relation in data['damage_relations']['double_damage_from']:
                    type_name = relation['name']
                    if type_name in all_weaknesses:
                        all_weaknesses[type_name] *= 2
                    else:
                        all_weaknesses[type_name] = 2
                for relation in data['damage_relations']['half_damage_from']:
                    type_name = relation['name']
                    if type_name in all_resistances:
                        all_resistances[type_name] *= 0.5
                    else:
                        all_resistances[type_name] = 0.5
                for relation in data['damage_relations']['no_damage_from']:
                    type_name = relation['name']
                    all_resistances[type_name] = 0
                TYPE_RELATIONS_CACHE.set(pokemon_type, {
                    'all_resistances': dict(all_resistances),
                    'all_weaknesses': dict(all_weaknesses)
                })
        except Exception as e:
            print(f"Error fetching type {pokemon_type}: {e}")
    resistances = []
    for type_name, multiplier in all_resistances.items():
        if multiplier <= 0.5:
            resistances.append({
                'type': type_name,
                'multiplier': str(multiplier).replace('0.5', '½').replace('0.25', '¼').replace('0.0', '0')
            })
    weaknesses = []
    for type_name, multiplier in all_weaknesses.items():
        if multiplier >= 2:
            weaknesses.append({
                'type': type_name,
                'multiplier': str(int(multiplier))
            })
    return {
        'resistances': resistances,
        'weaknesses': weaknesses
    }

def get_ability_details(ability_url, is_hidden=False):
    cached = ABILITY_CACHE.get(ability_url)
    if cached:
        result = dict(cached)
        result['is_hidden'] = is_hidden
        return result
    try:
        response = requests.get(ability_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            description = ""
            for entry in data['effect_entries']:
                if entry['language']['name'] == 'es':
                    description = entry['short_effect']
                    break
            if not description:
                for entry in data['effect_entries']:
                    if entry['language']['name'] == 'en':
                        description = entry['short_effect']
                        break
            result = {
                'name': data['name'].replace('-', ' ').title(),
                'description': description or "Descripción no disponible",
                'is_hidden': is_hidden
            }
            ABILITY_CACHE.set(ability_url, result)
            return result
    except Exception as e:
        print(f"Error fetching ability {ability_url}: {e}")
    return None

def get_all_sprites(sprites_data, key=None):
    cache_key = key or sprites_data.get('front_default')
    cached = SPRITES_CACHE.get(cache_key) if cache_key else None
    if cached:
        return cached
    sprites = {
        'front_default': sprites_data.get('front_default'),
        'front_shiny': sprites_data.get('front_shiny'),
        'front_female': sprites_data.get('front_female'),
        'front_shiny_female': sprites_data.get('front_shiny_female'),
        'back_default': sprites_data.get('back_default'),
        'back_shiny': sprites_data.get('back_shiny'),
        'back_female': sprites_data.get('back_female'),
        'back_shiny_female': sprites_data.get('back_shiny_female')
    }
    if cache_key:
        SPRITES_CACHE.set(cache_key, sprites)
    return sprites

def get_current_sprite(sprites, is_shiny, gender):
    if is_shiny and gender == 'female' and sprites.get('front_shiny_female'):
        return {'url': sprites['front_shiny_female'], 'description': 'Shiny - Hembra'}
    elif is_shiny and sprites.get('front_shiny'):
        return {'url': sprites['front_shiny'], 'description': 'Shiny - Macho'}
    elif not is_shiny and gender == 'female' and sprites.get('front_female'):
        return {'url': sprites['front_female'], 'description': 'Normal - Hembra'}
    elif sprites.get('front_default'):
        return {'url': sprites['front_default'], 'description': 'Normal - Macho'}
    else:
        return {'url': None, 'description': 'Sprite no disponible'}

def get_pokeinfo(index, data):
    name = data["name"].capitalize()
    abilities = [a["ability"]["name"] for a in data["abilities"]]
    height = data["height"]
    weight = data["weight"]
    types = [t["type"]["name"] for t in data["types"]]
    primary_type = types[0] if types else 'normal'
    type_color = get_type_color(primary_type)
    stats = []
    stat_names_map = {
        'hp': 'PS',
        'attack': 'Ataque',
        'defense': 'Defensa',
        'special-attack': 'Ataque Especial',
        'special-defense': 'Defensa Especial',
        'speed': 'Velocidad'
    }
    for stat_data in data["stats"]:
        stat_name = stat_data["stat"]["name"]
        stat_value = stat_data["base_stat"]
        display_name = stat_names_map.get(stat_name, stat_name.replace('-', ' ').title())
        stats.append(f"{display_name}: {stat_value}")
    pokemon_info = {
        'index': index,
        'name': name,
        'abilities': abilities,
        'height': height,
        'weight': weight,
        'types': types,
        'primary_type': primary_type,
        'type_color': type_color,
        'sprite': data.get('sprite'),
        'stats': stats
    }
    return pokemon_info

def one_pokemon(pokemon):
    data = get_pokedata(pokemon)
    if data:
        index = data["id"]
        return get_pokeinfo(index, data)
    return None

def get_region(region):
    cached = REGION_CACHE.get(region)
    if cached:
        return cached
    url = f"https://pokeapi.co/api/v2/generation/{region}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            REGION_CACHE.set(region, data)
            return data
    except Exception as e:
        print(f"Error fetching region {region}: {e}")
    return None

def get_region_info(region):
    region_key = region.lower()
    region_id = REGIONES.get(region_key)
    if not region_id:
        return None
    data = get_region(region_id)
    if not data:
        return None
    cached = REGION_CACHE.get(region_key)
    if cached and cached.get('pokemons'):
        return cached['pokemons']
    species = [p['name'] for p in data["pokemon_species"][:20]]  # Limitar a 20
    pokemons = []
    for species_name in species:
        pokedata = get_pokedata(species_name)
        if pokedata:
            info = get_pokeinfo(pokedata["id"], pokedata)
            pokemons.append(info)
    result = sorted(pokemons, key=lambda x: x['index']) if pokemons else None
    REGION_CACHE.set(region_key, {'pokemons': result})
    return result

def n_pokemons(rango):
    MAX_RANGE = 10  # Limitar a 10 en búsquedas
    pokemons = []
    if '-' in rango:
        rango = rango.replace(" ", "").split('-')
        try:
            if rango[0] == "" and rango[1] != "":
                start = 1
                finish = min(int(rango[1]), MAX_RANGE)
            elif rango[1] == "" and rango[0] != "":
                start = int(rango[0])
                finish = min(start + MAX_RANGE - 1, 1010)
            elif rango[0] != "" and rango[1] != "":
                start = int(rango[0])
                finish = min(int(rango[1]), start + MAX_RANGE - 1)
            else:
                return None
            if start <= 0 or finish <= 0 or start > finish:
                return None
        except ValueError:
            return None
        for i in range(start, finish + 1):
            data = get_pokedata(i)
            if data:
                pokemons.append(get_pokeinfo(i, data))
    elif ',' in rango:
        rango = rango.replace(" ", "").split(',')[:MAX_RANGE]
        for p in rango:
            data = get_pokedata(p)
            if data:
                pokemons.append(get_pokeinfo(data["id"], data))
    return pokemons

def get_random_pokemons(n):
    pokemons = []
    max_pokemon_id = 1010
    ids = random.sample(range(1, max_pokemon_id + 1), min(n, 6))  # Limitar a 6 en portada
    for poke_id in ids:
        data = get_pokedata(poke_id)
        if data:
            info = get_pokeinfo(data["id"], data)
            pokemons.append(info)
    return pokemons

@app.context_processor
def utility_processor():
    return dict(get_type_color=get_type_color)

@app.route('/')
def index():
    random_pokemons = get_random_pokemons(10)
    return render_template('index.html', random_pokemons=random_pokemons)

@app.route('/pokedex', methods=['GET', 'POST'])
def pokedex():
    if request.method == 'POST':
        valor = request.form.get('valor')
    elif request.method == 'GET':
        valor = request.args.get('valor')
    if not valor:
        return render_template('pokedex.html')
    if '-' in valor or ',' in valor:
        pokemons = n_pokemons(valor)
        return render_template('pokedex.html', varios=True, pokemons=pokemons)
    pokemon = []
    info = one_pokemon(valor)
    if info is None:
        region = get_region_info(valor)
        return render_template('pokedex.html', varios=True, pokemons=region)
    pokemon.append(info)
    return render_template('pokedex.html', varios=True, pokemons=pokemon)

@app.route('/pokedex/<pokemon_name>')
def pokemon_especifico(pokemon_name):
    pokemon = one_pokemon(pokemon_name.lower())
    if not pokemon:
        return redirect('/pokedex')
    data = get_pokedata(pokemon_name.lower())
    if data:
        stats = []
        for stat in data['stats']:
            stats.append({
                'name': stat['stat']['name'].replace('-', ' ').title(),
                'value': stat['base_stat']
            })
        pokemon['stats'] = stats
        damage_relations = get_damage_relations(pokemon['types'])
        pokemon['damage_relations'] = damage_relations
        ability_details = []
        for ability in data['abilities']:
            details = get_ability_details(ability['ability']['url'], ability['is_hidden'])
            if details:
                ability_details.append(details)
        pokemon['ability_details'] = ability_details
        pokemon['sprites'] = get_all_sprites(data.get('sprites', {}), key=pokemon_name.lower())
        initial_shiny = False
        initial_gender = 'male'
        pokemon['has_female_sprites'] = bool(
            pokemon['sprites'].get('front_female') or pokemon['sprites'].get('front_shiny_female'))
        pokemon['current_sprite'] = get_current_sprite(pokemon['sprites'], initial_shiny, initial_gender)
        pokemon['current_shiny'] = initial_shiny
        pokemon['current_gender'] = initial_gender
    return render_template('pokemon.html', pokemon_data=pokemon)

@app.route('/sprite/<pokemon_name>')
def get_sprite(pokemon_name):
    is_shiny = request.args.get('shiny', 'false').lower() == 'true'
    gender = request.args.get('gender', 'male')
    data = get_pokedata(pokemon_name.lower())
    if not data:
        return '<div class="sprite-not-available">Error al cargar sprite</div>', 404
    sprites = get_all_sprites(data.get('sprites', {}), key=pokemon_name.lower())
    current_sprite = get_current_sprite(sprites, is_shiny, gender)
    return render_template('sprite_partial.html',
                           sprite=current_sprite,
                           is_shiny=is_shiny,
                           gender=gender)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    try:
        messages = [
            {"role": "system", "content": """
             Eres IvAn, un experto asistente Pokémon.
             Tu tarea es ayudar a los usuarios con todo lo relacionado a Pokémon, incluyendo:
             - Recomendar equipos competitivos o para la aventura.
             - Dar información detallada sobre un Pokémon (tipos, habilidades, etc.).
             - Proporcionar enlaces a la página de un Pokémon específico. Por ejemplo, si el usuario pregunta por Bulbasaur,
               debes incluir un enlace en formato Markdown: [Bulbasaur](/pokedex/bulbasaur).
             - Tu tono debe ser amigable y útil.
             - Responde en español y mantén la consistencia.
             - Siempre incluye el enlace al Pokémon mencionado usando el formato [Nombre del Pokémon](/pokedex/nombre-del-pokemon).
             - Si el usuario pregunta por un Pokémon que no existe, responde con "Pokémon no encontrado".
             - Si el usuario pregunta por un Pokémon que no está en la Pokédex, responde con "Pokémon no encontrado".
             - Responder a preguntas sobre tipos, habilidades, estadísticas y ubicaciones de captura.
             """},
            {"role": "user", "content": user_message}
        ]
        response = client.chat.completions.create(
            model="z-ai/glm-4.5-air:free",
            messages=messages
        )
        ai_response = response.choices[0].message.content
        return jsonify({"response": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
