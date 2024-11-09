import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# Caricamento dei file CSV con percorso assoluto o relativo corretto
prenotazioni = pd.read_csv('prenotazioni.csv')  # Assicurati che il percorso sia corretto
veicoli = pd.read_csv('veicoli.csv')
disponibilita_ospedali = pd.read_csv('disponibilita_ospedali.csv')

# Aggiungi un ID univoco ai pazienti
prenotazioni['ID_paziente'] = range(1, len(prenotazioni) + 1)

# Conversione della colonna di orario in formato datetime
prenotazioni['orario_appuntamento'] = pd.to_datetime(prenotazioni['orario_appuntamento'], errors='coerce')

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

# Funzione per determinare l'ospedale più vicino a una città di partenza usando OpenStreetMap
def trova_ospedale_partenza(città_partenza):
    # Utilizza il geocoder Nominatim di OpenStreetMap
    geolocator = Nominatim(user_agent="ospedale_locator")
    location = geolocator.geocode(città_partenza)
    
    if not location:
        raise ValueError(f"Posizione per la città '{città_partenza}' non trovata tramite OpenStreetMap.")

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
    return abs(hash(città1) - hash(città2)) % 100

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





# Funzione per ordinare le città in base alla distanza dall'ospedale di partenza
def ordina_città_per_distanza(ospedale_partenza, percorso, posizioni_ospedali):
    # Ottieni le coordinate dell'ospedale di partenza
    coord_ospedale_partenza = posizioni_ospedali.get(ospedale_partenza)
    
    if not coord_ospedale_partenza:
        raise ValueError(f"Le coordinate per l'ospedale di partenza '{ospedale_partenza}' non sono disponibili.")
    
    # Calcola le distanze e ordina le città
    percorso_ordinato = sorted(
        percorso,
        key=lambda città: geodesic(coord_ospedale_partenza, posizioni_ospedali.get(città, (0, 0))).kilometers,
        reverse=True  # Ordinamento dalla più lontana alla più vicina
    )
    return percorso_ordinato

# Applicazione delle modifiche al DataFrame
def modifica_percorso_df(df, posizioni_ospedali):
    df['percorso'] = df.apply(lambda row: [città for città in row['percorso'].split(' -> ')
                                           if città not in [row['ospedale_partenza'], row['destinazione']]], axis=1)
    df['percorso_ordinato'] = df.apply(lambda row: ordina_città_per_distanza(
        row['ospedale_partenza'], row['percorso'], posizioni_ospedali), axis=1)
    # Trasforma la lista ordinata in una stringa con separatori per CSV
    df['percorso_ordinato'] = df['percorso_ordinato'].apply(lambda x: ' -> '.join(x))
    return df









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


# Implementazione completa del clustering, assegnazione veicoli e generazione output CSV
gruppi = raggruppa_pazienti(prenotazioni)
output_finale = []

for (destinazione, fascia_oraria), gruppo in gruppi:
    while len(gruppo) > 0:
        veicoli_selezionati = assegna_veicolo(gruppo)
        
        if not veicoli_selezionati:
            print("Attenzione: Nessun veicolo adatto disponibile per soddisfare i requisiti del gruppo.")
            break

        for veicolo_selezionato in veicoli_selezionati:
            # Capacità del veicolo selezionato
            num_barelle = capacità_veicoli[veicolo_selezionato]['barella']
            num_sedia_rotelle = capacità_veicoli[veicolo_selezionato]['sedia_rotelle']
            num_abili = capacità_veicoli[veicolo_selezionato]['abili']
            
            pazienti_selezionati = []
            for _, paziente in gruppo.iterrows():
                if paziente['tipo_paziente'] == 'barella' and num_barelle > 0:
                    pazienti_selezionati.append(paziente)
                    num_barelle -= 1
                elif paziente['tipo_paziente'] == 'sedia a rotelle' and num_sedia_rotelle > 0:
                    pazienti_selezionati.append(paziente)
                    num_sedia_rotelle -= 1
                elif paziente['tipo_paziente'] == 'abile' and num_abili > 0:
                    pazienti_selezionati.append(paziente)
                    num_abili -= 1

            # Rimuovi i pazienti selezionati dal gruppo
            # Usa l'attributo ID_paziente per rimuovere le righe in modo più sicuro
            gruppo = gruppo.drop(gruppo[gruppo['ID_paziente'].isin([p['ID_paziente'] for p in pazienti_selezionati])].index)
 
            
            # Crea un percorso per i pazienti selezionati
            città_partenza = [p['città_partenza'] for p in pazienti_selezionati]
            matrice_distanza = crea_matrice_distanza(città_partenza + [destinazione])
            percorso = trova_percorso_ottimale(matrice_distanza, len(pazienti_selezionati))
            
            # Mappatura degli indici delle città ai nomi reali
            città_mapping = {i: città for i, città in enumerate(città_partenza + [destinazione])}
            percorso_nomi = [città_mapping[idx] for idx in percorso]

            id_pazienti_percorso = [p['ID_paziente'] for p in pazienti_selezionati]
            
            ospedale_partenza = trova_ospedale_partenza(città_partenza[0]) if città_partenza else None
            
            output_finale.append({
                'ospedale_partenza': ospedale_partenza,
                'destinazione': destinazione,
                'fascia_oraria': fascia_oraria,
                'percorso': percorso_nomi,
                'id_pazienti': id_pazienti_percorso,
                'num_pazienti': len(pazienti_selezionati),
                'tipo_veicolo': veicolo_selezionato
            })
# Salvataggio su CSV
output_df = pd.DataFrame(output_finale)

output_df['percorso'] = output_df.apply(
    lambda row: list({p for p in row['percorso'] if p not in [row['ospedale_partenza'], row['destinazione']]}),
    axis=1
)

# Scrittura del DataFrame modificato su file CSV
output_df.to_csv('trasporti_ottimizzati.csv', index=False)


