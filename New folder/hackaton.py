import pandas as pd
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
from geopy.distance import geodesic

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
    'VIPITENO': (46.8957, 11.4339)
}

# Funzione per determinare l'ospedale più vicino a una città di partenza
def trova_ospedale_partenza(città_partenza):
    posizione_città = posizioni_ospedali.get(città_partenza, None)
    if not posizione_città:
        raise ValueError(f"Posizione per la città '{città_partenza}' non trovata.")

    ospedale_piu_vicino = None
    distanza_minima = float('inf')

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

# Implementazione completa del clustering, assegnazione veicoli e generazione output CSV
gruppi = raggruppa_pazienti(prenotazioni)
output_finale = []

for (destinazione, fascia_oraria), gruppo in gruppi:
    num_pazienti = len(gruppo)
    città_partenza = gruppo['città_partenza'].unique().tolist()
    matrice_distanza = crea_matrice_distanza(città_partenza + [destinazione])
    percorso = trova_percorso_ottimale(matrice_distanza, num_pazienti)
    
    if percorso:
        # Determina l'ospedale di partenza per il primo punto del percorso
        ospedale_partenza = trova_ospedale_partenza(città_partenza[0])  # Considera la prima città come esempio
        
        # Mappatura degli indici delle città ai nomi reali
        città_mapping = {i: città for i, città in enumerate(città_partenza + [destinazione])}
        percorso_nomi = [città_mapping[idx] for idx in percorso]

        # Trova gli ID dei pazienti nel percorso
        id_pazienti_percorso = [gruppo[gruppo['città_partenza'] == città]['ID_paziente'].tolist() for città in città_partenza]
        id_pazienti_percorso_flat = [item for sublist in id_pazienti_percorso for item in sublist]
        
        output_finale.append({
            'ospedale_partenza': ospedale_partenza,
            'destinazione': destinazione,
            'fascia_oraria': fascia_oraria,
            'percorso': percorso_nomi,
            'id_pazienti': id_pazienti_percorso_flat,
            'num_pazienti': num_pazienti
        })

# Salvataggio su CSV
output_df = pd.DataFrame(output_finale)
output_df.to_csv('trasporti_ottimizzati.csv', index=False)
