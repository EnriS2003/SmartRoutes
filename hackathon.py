import pandas as pd
import osmnx as ox

from hackathon_helper import *


ox.settings.log_console=True
prenotazioni = pd.read_csv('resources/prenotazioni.csv')



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


# Applica la funzione al DataFrame
output_df['percorso'] = output_df.apply(ordina_per_distanza, axis=1)
output_df['fascia_oraria'] = pd.to_datetime(output_df['fascia_oraria'], format='%Y-%m-%d %H:%M:%S')

# Funzione per calcolare l'orario di partenza
output_df['orario_partenza'] = output_df.apply(
    lambda row: calcola_orario_partenza(
        row['fascia_oraria'],
        row['ospedale_partenza'],
        row['percorso'],
        row['destinazione']
    )[0] if calcola_orario_partenza(
        row['fascia_oraria'],
        row['ospedale_partenza'],
        row['percorso'],
        row['destinazione']
    ) else None,
    axis=1
)


# Scrittura del DataFrame modificato su file CSV
output_df.to_csv('resources/trasporti_ottimizzati.csv', index=False)

