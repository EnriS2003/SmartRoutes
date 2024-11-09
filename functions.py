
import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from geopy.distance import geodesic
from geopy.geocoders import Nominatim


posizioni_ospedali = {
    'BOLZANO': (46.4983, 11.3548),
    'BRESSANONE': (46.7176, 11.6565),
    'MERANO': (46.6713, 11.1594),
    'BRUNICO': (46.7962, 11.9365),
    'VIPITENO': (46.8957, 11.4339),
    'SILANDRO': (46.6267, 10.7725),
    'SAN CANDIDO': (46.7332, 12.2843)
}

disponibilita_veicoli_ospedale = {
    'BOLZANO': {'KTW': 10, 'MFF1': 4, 'MFF2': 22, 'PKW': 6},
    'BRESSANONE': {'KTW': 4, 'MFF1': 12, 'MFF2': 1, 'PKW': 7},
    'MERANO': {'KTW': 3, 'MFF1': 9, 'MFF2': 21, 'PKW': 18},
    'BRUNICO': {'KTW': 1, 'MFF1': 7, 'MFF2': 5, 'PKW': 8},
    'VIPITENO': {'KTW': 12, 'MFF1': 4, 'MFF2': 1, 'PKW': 11}
}








# Funzione per trovare l'ospedale più vicino a una città di partenza
def trova_ospedale_partenza(città_partenza):
    geolocator = Nominatim(user_agent="ospedale_locator")
    location = geolocator.geocode(città_partenza)
    
    if not location:
        return f"Non è stato possibile trovare la città: {città_partenza}"

    coord_città = (location.latitude, location.longitude)
    
    ospedale_più_vicino = None
    distanza_minima = float('inf')
    
    for nome_ospedale, coord_ospedale in posizioni_ospedali.items():
        distanza = geodesic(coord_città, coord_ospedale).kilometers
        if distanza < distanza_minima:
            distanza_minima = distanza
            ospedale_più_vicino = nome_ospedale
    
    return ospedale_più_vicino


    
    trasporti = []

    # Raggruppa i pazienti per città di appuntamento e fascia oraria
    for (città_appuntamento, orario), gruppo in prenotazioni_df.groupby(['città_appuntamento', 'fascia_oraria']):
        pazienti_per_tipo = gruppo.groupby('tipo_paziente')['ID_paziente'].apply(list).to_dict()
        
        veicoli_assegnati = []

        # Tenta di assegnare pazienti ai veicoli disponibili in modo ottimale
        while any(len(ids) > 0 for ids in pazienti_per_tipo.values()):  # Continua finché ci sono pazienti da trasportare
            veicolo_usato = False
            veicolo = {'tipo_veicolo': None, 'pazienti': []}
            
            for tipo_veicolo, capacità in capacità_veicoli.items():
                veicolo_usato = False
                pazienti_in_veicolo = {'abili': 0, 'sedia a rotelle': 0, 'barella': 0}
                pazienti_ids_in_veicolo = []

                for tipo_paziente, ids in pazienti_per_tipo.items():
                    if len(ids) > 0 and capacità.get(tipo_paziente, 0) > 0:
                        # Numero di pazienti che possono essere caricati in questo veicolo
                        num_trasportati = min(len(ids), capacità[tipo_paziente] - pazienti_in_veicolo[tipo_paziente])
                        if num_trasportati > 0:
                            pazienti_in_veicolo[tipo_paziente] += num_trasportati
                            pazienti_ids_in_veicolo.extend(ids[:num_trasportati])
                            pazienti_per_tipo[tipo_paziente] = ids[num_trasportati:]
                            veicolo_usato = True
                            veicolo['pazienti'].extend([(tipo_paziente, id_paziente) for id_paziente in ids[:num_trasportati]])

                if veicolo_usato:
                    veicolo['tipo_veicolo'] = tipo_veicolo
                    veicoli_assegnati.append(veicolo)
                    trasporti.append({
                        'città_appuntamento': città_appuntamento,
                        'fascia_oraria': orario,
                        'tipo_veicolo': tipo_veicolo,
                        'pazienti': veicolo['pazienti']
                    })
                    break  # Passa al prossimo veicolo necessario

    return pd.DataFrame(trasporti)