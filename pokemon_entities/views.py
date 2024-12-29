import folium
import json

from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone
from .models import Pokemon, PokemonEntity

MOSCOW_CENTER = [55.751244, 37.618423]
DEFAULT_IMAGE_URL = (
    'https://vignette.wikia.nocookie.net/pokemon/images/6/6e/%21.png/revision'
    '/latest/fixed-aspect-ratio-down/width/240/height/240?cb=20130525215832'
    '&fill=transparent'
)


def add_pokemon(folium_map, lat, lon, image_url=DEFAULT_IMAGE_URL):
    icon = folium.features.CustomIcon(
        image_url,
        icon_size=(50, 50),
    )
    folium.Marker(
        [lat, lon],
        # Warning! `tooltip` attribute is disabled intentionally
        # to fix strange folium cyrillic encoding bug
        icon=icon,
    ).add_to(folium_map)


def show_all_pokemons(request):
    folium_map = folium.Map(location=MOSCOW_CENTER, zoom_start=12)

    current_time = timezone.localtime()
    pokemon_entities = PokemonEntity.objects.filter(
        appeared_at__lte=current_time,
        disappeared_at__gte=current_time
    )

    for entity in pokemon_entities:
        if entity.pokemon.image:
            image_url = request.build_absolute_uri(entity.pokemon.image.url)
        else:
            image_url = DEFAULT_IMAGE_URL

        add_pokemon(
            folium_map,
            entity.latitude,
            entity.longitude,
            image_url
        )

    pokemons_on_page = []
    for pokemon in Pokemon.objects.all():
        if pokemon.image:
            img_url = request.build_absolute_uri(pokemon.image.url)
        else:
            img_url = DEFAULT_IMAGE_URL

        pokemons_on_page.append({
            'pokemon_id': pokemon.id,
            'img_url': img_url,
            'title_ru': pokemon.title,
        })

    return render(request, 'mainpage.html', context={
        'map': folium_map._repr_html_(),
        'pokemons': pokemons_on_page,
    })


def show_pokemon(request, pokemon_id):
    pokemon = get_object_or_404(Pokemon, id=pokemon_id)

    folium_map = folium.Map(location=MOSCOW_CENTER, zoom_start=12)

    current_time = timezone.localtime()
    pokemon_entities = PokemonEntity.objects.filter(
        pokemon=pokemon,
        appeared_at__lte=current_time,
        disappeared_at__gte=current_time
    )

    for entity in pokemon_entities:
        entity_image_url = (request.build_absolute_uri(entity.pokemon.image.url) if entity.pokemon.image else DEFAULT_IMAGE_URL)
        add_pokemon(
            folium_map,
            entity.latitude,
            entity.longitude,
            entity_image_url
        )

    pokemon_details = {
        'pokemon_id': pokemon.id,
        'title_ru': pokemon.title,
        'title_en': pokemon.title_en,
        'title_jp': pokemon.title_jp,
        'description': pokemon.description,
        'img_url': (request.build_absolute_uri(pokemon.image.url) if pokemon.image else DEFAULT_IMAGE_URL),
        'entities': [],
    }

    for entity in pokemon_entities:
        pokemon_details['entities'].append({
            'level': entity.level,
            'lat': entity.latitude,
            'lon': entity.longitude,
        })

    if pokemon.previous_evolution:
        pokemon_details['previous_evolution'] = {
            'pokemon_id': pokemon.previous_evolution.id,
            'title_ru': pokemon.previous_evolution.title,
            'img_url': request.build_absolute_uri(pokemon.previous_evolution.image.url) if pokemon.previous_evolution.image else DEFAULT_IMAGE_URL
        }

    next_evolution = pokemon.next_evolutions.first()
    if next_evolution:
        pokemon_details['next_evolution'] = {
            'pokemon_id': next_evolution.id,
            'title_ru': next_evolution.title,
            'img_url': request.build_absolute_uri(next_evolution.image.url) if next_evolution.image else DEFAULT_IMAGE_URL
        }

    return render(request, 'pokemon.html', context={
        'map': folium_map._repr_html_(),
        'pokemon': pokemon_details
    })