import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import osmnx as ox
import networkx as nx
from datetime import datetime, timedelta
import requests


geolocator = Nominatim(user_agent="geo_app")



# Posizioni geografiche degli ospedali
posizioni_ospedali = {
    'BOLZANO': (46.4983, 11.3548),
    'BRESSANONE': (46.7176, 11.6565),
    'MERANO': (46.6713, 11.1594),
    'BRUNICO': (46.7962, 11.9365),
    'VIPITENO': (46.8957, 11.4339),
    'SILANDRO': (46.6267, 10.7725),
    'SAN CANDIDO': (46.7332, 12.2843)
}


# Capacità dei veicoli
capacità_veicoli = {
    'KTW': {'barella': 1, 'sedia_rotelle': 1, 'abili': 2},
    'MFF1': {'barella': 0, 'sedia_rotelle': 1, 'abili': 4},
    'MFF2': {'barella': 0, 'sedia_rotelle': 2, 'abili': 3},
    'PKW': {'barella': 0, 'sedia_rotelle': 0, 'abili': 4}
}


# Funzione per ottenere le coordinate di una città
def get_coordinates(city):
    if city in posizioni_ospedali:
        print(f"Debug: Coordinate di {city} ottenute da coordinate fisse = {posizioni_ospedali[city]}")
        return posizioni_ospedali[city]
    
    location = geolocator.geocode(city)
    if location:
        print(f"Debug: Coordinate di {city} = ({location.latitude}, {location.longitude})")
        return (location.latitude, location.longitude)
    else:
        print(f"Debug: Coordinate non trovate per {city}")
        return None

# Funzione per determinare l'ospedale più vicino a una città di partenza usando OpenStreetMap
def trova_ospedale_partenza(città_partenza):
    geolocator = Nominatim(user_agent="ospedale_locator")
    location = geolocator.geocode(città_partenza)
    
    if not location: raise ValueError(f"Posizione per la città '{città_partenza}' non trovata tramite OpenStreetMap.")

    posizione_città = (location.latitude, location.longitude)
    
    ospedale_piu_vicino = None
    distanza_minima = float('inf')

    # Itera sulle posizioni degli ospedali per trovare quello più vicino
    for ospedale, posizione in posizioni_ospedali.items():
        distanza = geodesic(posizione_città, posizione).kilometers
        if distanza < distanza_minima:
            distanza_minima = distanza
            ospedale_piu_vicino = ospedale

    return ospedale_piu_vicino

# Funzione per raggruppare pazienti per destinazione e fascia oraria
def raggruppa_pazienti(prenotazioni):
    prenotazioni['fascia_oraria'] = prenotazioni['orario_appuntamento'].dt.floor('30min')
    gruppi = prenotazioni.groupby(['città_appuntamento', 'fascia_oraria'])
    return gruppi

# Funzione per calcolare la distanza tra le città (placeholder)
def calcola_distanza(città1, città2):
    coords1 = get_coordinates(città1)
    coords2 = get_coordinates(città2)

    if coords1 and coords2:
        return geodesic(coords1, coords2).kilometers
    else:
        return None  # Restituisce None se non si riescono a ottenere le coordinate di una città

# Funzione per creare la matrice di distanza
def crea_matrice_distanza(città):
    matrice = [[calcola_distanza(c1, c2) for c2 in città] for c1 in città]
    return matrice

# Funzione per trovare il percorso ottimale
def trova_percorso_ottimale(matrice_distanza, num_pazienti):
    manager = pywrapcp.RoutingIndexManager(len(matrice_distanza), 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    def distanza_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return matrice_distanza[from_node][to_node]
    transit_callback_index = routing.RegisterTransitCallback(distanza_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        percorso = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            percorso.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        percorso.append(manager.IndexToNode(index))
        return percorso
    else:
        return None

# Funzione aggiornata per assegnare veicoli ai gruppi di pazienti
def assegna_veicolo(gruppo):
    num_barelle = sum(gruppo['tipo_paziente'] == 'barella')
    num_sedia_rotelle = sum(gruppo['tipo_paziente'] == 'sedia a rotelle')
    num_abili = sum(gruppo['tipo_paziente'] == 'abile')

    veicoli_usati = []

    while num_barelle > 0 or num_sedia_rotelle > 0 or num_abili > 0:
        for veicolo, capacità in capacità_veicoli.items():
            if (num_barelle <= capacità['barella'] and 
                num_sedia_rotelle <= capacità['sedia_rotelle'] and 
                num_abili <= capacità['abili']):
                # Aggiorna il numero di pazienti rimanenti
                num_barelle -= min(num_barelle, capacità['barella'])
                num_sedia_rotelle -= min(num_sedia_rotelle, capacità['sedia_rotelle'])
                num_abili -= min(num_abili, capacità['abili'])
                
                veicoli_usati.append(veicolo)
                break
        else:
            # Se nessun veicolo può trasportare l'intero gruppo, si riduce la dimensione e si continua
            if num_barelle > 0:
                num_barelle -= 1
            elif num_sedia_rotelle > 0:
                num_sedia_rotelle -= 1
            elif num_abili > 0:
                num_abili -= 1

    return veicoli_usati  # Restituisce la lista dei veicoli usati





def ordina_per_distanza(row):
    ospedale_partenza = row['ospedale_partenza']
    percorso = row['percorso']

    # Ottieni le coordinate dell'ospedale di partenza
    start_coords = get_coordinates(ospedale_partenza)

    if start_coords:
        # Calcola la distanza di ogni città nel percorso rispetto all'ospedale di partenza
        city_distances = []
        for city in percorso:
            city_coords = get_coordinates(city)
            if city_coords:
                distance = geodesic(start_coords, city_coords).kilometers
                city_distances.append((city, distance))
                print(f"Debug: Distanza tra {ospedale_partenza} e {city} = {distance:.2f} km")

        # Ordina le città in base alla distanza in ordine decrescente
        city_distances.sort(key=lambda x: x[1], reverse=True)
        sorted_cities = [city[0] for city in city_distances]

        print(f"Debug: Città ordinate per distanza da {ospedale_partenza}: {sorted_cities}")

        return sorted_cities
    else:
        print(f"Debug: Coordinate non trovate per {ospedale_partenza}. Restituzione del percorso originale.")
        return percorso


# Funzione per calcolare il tempo di viaggio tra due coordinate usando OSRM
def calcola_tempo_viaggio_osrm(origine, destinazione):
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{origine[1]},{origine[0]};{destinazione[1]},{destinazione[0]}"
    params = {
        'overview': 'full',
        'geometries': 'geojson'
    }
    response = requests.get(osrm_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['routes']:
            durata_viaggio = data['routes'][0]['duration']  # Durata in secondi
            return durata_viaggio
        else:
            print("Nessun percorso trovato.")
            return None
    else:
        print(f"Errore nel calcolo del percorso: {response.status_code}")
        return None

# Funzione principale per calcolare l'orario di partenza
def calcola_orario_partenza(orario_arrivo, punto_partenza, percorso, destinazione):
    # Converti i punti in coordinate
    partenza_coords = get_coordinates(punto_partenza)
    destinazione_coords = get_coordinates(destinazione)
    percorso_coords = [get_coordinates(città) for città in percorso]

    if None in [partenza_coords, destinazione_coords] or any(coord is None for coord in percorso_coords):
        print("Errore: coordinate mancanti per alcune città.")
        return None

    # Calcola il tempo totale di viaggio sommando i tempi tra i punti
    tempo_totale_trascorso = 0
    punti_intermedi = [partenza_coords] + percorso_coords + [destinazione_coords]

    for i in range(len(punti_intermedi) - 1):
        durata_segmento = calcola_tempo_viaggio_osrm(punti_intermedi[i], punti_intermedi[i + 1])
        if durata_segmento:
            tempo_totale_trascorso += durata_segmento
        else:
            print(f"Errore nel calcolo del tempo di viaggio tra {punti_intermedi[i]} e {punti_intermedi[i + 1]}")
            return None

    # Calcola l'orario di partenza
    tempo_totale_trascorso_minuti = timedelta(seconds=tempo_totale_trascorso)
    orario_partenza = orario_arrivo - tempo_totale_trascorso_minuti

    return orario_partenza, tempo_totale_trascorso_minuti


