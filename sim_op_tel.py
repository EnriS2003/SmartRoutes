import pandas as pd
from datetime import datetime
import os

class GestorePrenotazioni:
    def __init__(self):
        self.ospedali = [
            'BOLZANO', 'MERANO', 'BRESSANONE', 'BRUNICO', 
            'VIPITENO', 'SILANDRO', 'SAN CANDIDO'
        ]
        
        self.tipi_paziente = [
            'barella',
            'sedia a rotelle',
            'deambulante con accompagnamento',
            'deambulante autonomo'
        ]

    def richiedi_data_ora(self):
        """Richiede data e ora della prenotazione"""
        while True:
            try:
                data = input("Data (gg/mm/aaaa): ")
                ora = input("Ora (hh:mm): ")
                # Verifica il formato
                datetime.strptime(f"{data} {ora}", "%d/%m/%Y %H:%M")
                return data, ora
            except ValueError:
                print("⚠️ Formato data/ora non valido. Riprova.")

    def richiedi_ospedale(self, messaggio):
        """Richiede e valida la scelta dell'ospedale"""
        while True:
            print(f"\n{messaggio}")
            for i, ospedale in enumerate(self.ospedali, 1):
                print(f"{i}. {ospedale}")
            
            try:
                scelta = int(input("\nScelta (numero): "))
                if 1 <= scelta <= len(self.ospedali):
                    return self.ospedali[scelta-1]
                print("⚠️ Scelta non valida")
            except ValueError:
                print("⚠️ Inserire un numero")

    def richiedi_tipo_paziente(self):
        """Richiede e valida il tipo di paziente"""
        while True:
            print("\nTipo di paziente:")
            for i, tipo in enumerate(self.tipi_paziente, 1):
                print(f"{i}. {tipo}")
            
            try:
                scelta = int(input("\nScelta (numero): "))
                if 1 <= scelta <= len(self.tipi_paziente):
                    return self.tipi_paziente[scelta-1]
                print("⚠️ Scelta non valida")
            except ValueError:
                print("⚠️ Inserire un numero")

    def registra_prenotazione(self):
        """Registra una nuova prenotazione"""
        print("\n=== Nuova Prenotazione Trasporto ===")
        
        # Raccolta dati paziente
        nome = input("Nome paziente: ")
        cognome = input("Cognome paziente: ")
        telefono = input("Telefono: ")
        
        # Raccolta data e ora
        data, ora = self.richiedi_data_ora()
        
        # Raccolta località
        citta_partenza = input("Città di partenza: ")
        indirizzo_partenza = input("Indirizzo di partenza: ")
        
        # Selezione ospedale
        ospedale = self.richiedi_ospedale("Ospedale di destinazione:")
        
        # Tipo paziente
        tipo_paziente = self.richiedi_tipo_paziente()
        
        # Note aggiuntive
        note = input("\nNote aggiuntive (opzionale): ")
        
        return {
            'nome': nome,
            'cognome': cognome,
            'telefono': telefono,
            'data_prenotazione': data,
            'ora_prenotazione': ora,
            'citta_partenza': citta_partenza,
            'indirizzo_partenza': indirizzo_partenza,
            'ospedale_destinazione': ospedale,
            'tipo_paziente': tipo_paziente,
            'note': note,
            'timestamp_registrazione': datetime.now().strftime("%d/%m/%Y %H:%M")
        }

    def salva_prenotazione(self, dati):
        """Salva la prenotazione nel CSV"""
        try:
            df = pd.DataFrame([dati])
            file_exists = os.path.isfile('resources/prenotazioni.csv')
            
            df.to_csv('resources/prenotazioni.csv', 
                     mode='a', 
                     header=not file_exists, 
                     index=False)
            
            print("\n✅ Prenotazione salvata con successo!")
            return True
        except Exception as e:
            print(f"\n❌ Errore nel salvataggio: {e}")
            return False

def main():
    gestore = GestorePrenotazioni()
    
    while True:
        print("\n=== Gestione Prenotazioni Trasporti ===")
        print("1. Nuova prenotazione")
        print("2. Visualizza prenotazioni")
        print("3. Esci")
        
        scelta = input("\nScelta: ")
        
        if scelta == "1":
            dati = gestore.registra_prenotazione()
            
            # Mostra riepilogo
            print("\nRiepilogo prenotazione:")
            for chiave, valore in dati.items():
                print(f"{chiave}: {valore}")
            
            if input("\nConfermi il salvataggio? (s/n): ").lower() == 's':
                gestore.salva_prenotazione(dati)
        
        elif scelta == "2":
            try:
                df = pd.read_csv('prenotazioni_trasporti.csv')
                print("\nPrenotazioni registrate:")
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                print(df)
            except FileNotFoundError:
                print("Nessuna prenotazione trovata")
        
        elif scelta == "3":
            print("Arrivederci!")
            break
        
        else:
            print("Scelta non valida")

if __name__ == "__main__":
    main()

import pandas as pd
df = pd.read_csv('prenotazioni_trasporti.csv')
print(df)
