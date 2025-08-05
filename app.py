from flask import Flask, redirect, render_template, request, jsonify
import requests
import random
from openai import OpenAI

app = Flask(__name__)

# Configuración del cliente de OpenAI para "IvAn"
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="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" 
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


def get_pokedata(pokemon):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def get_type_color(pokemon_type):
    """Retorna el color hexadecimal basado en el tipo del Pokémon"""
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
    """Obtiene las relaciones de daño para los tipos del Pokémon"""
    all_resistances = {}
    all_weaknesses = {}

    for pokemon_type in pokemon_types:
        url = f"https://pokeapi.co/api/v2/type/{pokemon_type}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            # Procesar debilidades (double damage from)
            for relation in data['damage_relations']['double_damage_from']:
                type_name = relation['name']
                if type_name in all_weaknesses:
                    all_weaknesses[type_name] *= 2  # Si ya existe, multiplicar
                else:
                    all_weaknesses[type_name] = 2

            # Procesar resistencias (half damage from)
            for relation in data['damage_relations']['half_damage_from']:
                type_name = relation['name']
                if type_name in all_resistances:
                    all_resistances[type_name] *= 0.5
                else:
                    all_resistances[type_name] = 0.5

            # Procesar inmunidades (no damage from)
            for relation in data['damage_relations']['no_damage_from']:
                type_name = relation['name']
                all_resistances[type_name] = 0

    # Convertir a formato para el template
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
    """Obtiene detalles de una habilidad"""
    response = requests.get(ability_url)
    if response.status_code == 200:
        data = response.json()
        description = ""

        # Buscar descripción en español primero, luego inglés
        for entry in data['effect_entries']:
            if entry['language']['name'] == 'es':
                description = entry['short_effect']
                break

        if not description:
            for entry in data['effect_entries']:
                if entry['language']['name'] == 'en':
                    description = entry['short_effect']
                    break

        return {
            'name': data['name'].replace('-', ' ').title(),
            'description': description or "Descripción no disponible",
            'is_hidden': is_hidden
        }
    return None


def get_all_sprites(sprites_data):
    return {
        'front_default': sprites_data.get('front_default'),
        'front_shiny': sprites_data.get('front_shiny'),
        'front_female': sprites_data.get('front_female'),
        'front_shiny_female': sprites_data.get('front_shiny_female'),
        'back_default': sprites_data.get('back_default'),
        'back_shiny': sprites_data.get('back_shiny'),
        'back_female': sprites_data.get('back_female'),
        'back_shiny_female': sprites_data.get('back_shiny_female')
    }


def get_current_sprite(sprites, is_shiny, gender):
    """Determina qué sprite mostrar basado en los parámetros"""
    if is_shiny and gender == 'female' and sprites.get('front_shiny_female'):
        return {
            'url': sprites['front_shiny_female'],
            'description': 'Shiny - Hembra'
        }
    elif is_shiny and sprites.get('front_shiny'):
        return {
            'url': sprites['front_shiny'],
            'description': 'Shiny - Macho'
        }
    elif not is_shiny and gender == 'female' and sprites.get('front_female'):
        return {
            'url': sprites['front_female'],
            'description': 'Normal - Hembra'
        }
    elif sprites.get('front_default'):
        return {
            'url': sprites['front_default'],
            'description': 'Normal - Macho'
        }
    else:
        return {
            'url': None,
            'description': 'Sprite no disponible'
        }


def get_pokeinfo(index, data):
    name = data["name"].capitalize()
    abilities = [a["ability"]["name"] for a in data["abilities"]]
    height = data["height"]
    weight = data["weight"]
    types = [t["type"]["name"] for t in data["types"]]

    # Obtener ubicaciones
    locations_url = data.get("location_area_encounters", f"https://pokeapi.co/api/v2/pokemon/{index}/encounters")
    locations = []
    try:
        loc_response = requests.get(locations_url)
        if loc_response.status_code == 200:
            loc_data = loc_response.json()
            for loc in loc_data:
                loc_name = loc["location_area"]["name"].replace("-", " ").title()
                locations.append(loc_name)
    except Exception:
        locations = []

    # Obtener el color del tipo principal
    primary_type = types[0] if types else 'normal'
    type_color = get_type_color(primary_type)

    # Obtener estadísticas
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

    # Obtener todos los sprites
    sprites = get_all_sprites(data.get('sprites', {}))

    pokemon_info = {
        'index': index,
        'name': name,
        'abilities': abilities,
        'height': height,
        'weight': weight,
        'types': types,
        'primary_type': primary_type,
        'type_color': type_color,
        'locations': locations,
        'sprite': sprites['front_default'],
        'sprites': sprites,  # Todos los sprites disponibles, en caso de shiny o género
        'back_sprite': sprites['back_default'],
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
    url = f"https://pokeapi.co/api/v2/generation/{region}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
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

    for species_name in species:
        try:
            pokedata = get_pokedata(species_name)
            if pokedata:
                info = get_pokeinfo(pokedata["id"], pokedata)
                pokemons.append(info)
        except:
            continue

    return sorted(pokemons, key=lambda x: x['index']) if pokemons else None


def n_pokemons(rango):
    pokemons = []

    if '-' in rango:
        rango = rango.replace(" ", "").split('-')
        try:
            if rango[0] == "" and rango[1] != "":
                start = 1
                finish = int(rango[1])
            elif rango[1] == "" and rango[0] != "":
                start = int(rango[0])
                finish = 1025
            elif rango[0] != "" and rango[1] != "":
                start = int(rango[0])
                finish = int(rango[1])
            else:
                return None

            if start <= 0 or finish <= 0 or start > finish:
                return None

        except ValueError:
            return None

        for i in range(start, finish + 1):
            try:
                data = get_pokedata(i)
                if data:
                    pokemons.append(get_pokeinfo(i, data))
            except:
                continue

    elif ',' in rango:
        rango = rango.replace(" ", "").split(',')
        for p in rango:
            try:
                data = get_pokedata(p)
                if data:
                    index = data["id"]
                    pokemons.append(get_pokeinfo(index, data))
            except:
                continue

    return pokemons


def get_random_pokemons(n):
    """Obtiene n pokémons aleatorios usando la pokeapi"""
    pokemons = []
    max_pokemon_id = 1010
    ids = random.sample(range(1, max_pokemon_id + 1), n)

    for poke_id in ids:
        try:
            data = get_pokedata(poke_id)
            if data:
                info = get_pokeinfo(data["id"], data)
                pokemons.append(info)
        except:
            continue
    return pokemons


@app.context_processor
def utility_processor():
    return dict(get_type_color=get_type_color)


@app.route('/')
def index():
    random_pokemons = get_random_pokemons(10)
    for pokemon in random_pokemons:
        print(f"- {pokemon['name']} (#{pokemon['index']})")
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
    """Ruta para mostrar detalles específicos de un Pokémon"""
    pokemon = one_pokemon(pokemon_name.lower())
    if not pokemon:
        return redirect('/pokedex')

    # Obtener datos adicionales
    data = get_pokedata(pokemon_name.lower())
    if data:
        # Convertir estadísticas a formato para template
        stats = []
        for stat in data['stats']:
            stats.append({
                'name': stat['stat']['name'].replace('-', ' ').title(),
                'value': stat['base_stat']
            })
        pokemon['stats'] = stats

        # Obtener relaciones de daño
        damage_relations = get_damage_relations(pokemon['types'])
        pokemon['damage_relations'] = damage_relations

        # Obtener detalles de habilidades
        ability_details = []
        for ability in data['abilities']:
            details = get_ability_details(ability['ability']['url'], ability['is_hidden'])
            if details:
                ability_details.append(details)
        pokemon['ability_details'] = ability_details

        # Actualizar sprites con todos los disponibles
        pokemon['sprites'] = get_all_sprites(data.get('sprites', {}))

        # Configuración inicial del sprite (ESTADO INICIAL CORRECTO)
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
    """Ruta HTMX para obtener sprites dinámicamente"""
    is_shiny = request.args.get('shiny', 'false').lower() == 'true'
    gender = request.args.get('gender', 'male')

    # Obtener datos del Pokémon
    data = get_pokedata(pokemon_name.lower())
    if not data:
        return '<div class="sprite-not-available">Error al cargar sprite</div>', 404

    sprites = get_all_sprites(data.get('sprites', {}))
    current_sprite = get_current_sprite(sprites, is_shiny, gender)

    return render_template('sprite_partial.html',
                           sprite=current_sprite,
                           is_shiny=is_shiny,
                           gender=gender)


@app.route('/chat', methods=['POST'])
def chat():
    """Ruta para manejar el chat con IA - IvAn"""
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
    app.run(debug=True, host='0.0.0.0')