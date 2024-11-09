from flask import Flask, render_template, session, request, redirect, url_for, flash
import pandas as pd
from geopy.geocoders import Nominatim
from datetime import timedelta
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = 'hfuendidh3qq89rh49fnvsfrugb4urw9qiefbuwe' #NOTA: usa una chiave sicura 
#app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_USE_SIGNER'] = True

#Se si lavora con più worker es:gunicorn aiuta a sincronizzarli per non perdere i dati sessione
#app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379, db=0) 


# Crea una sessione HTTP
session = requests.Session()

# ATTENZIONE: SOSTITUIRE L'ARCHIVIAZIONE DEI DATI UTENTE IN UN DB SICURO IN AMBIENTE PROD (es: istnaza RDS con crittografia)
credentials = {
    "user1": "password123", # ATTENZIONE: utiizzare funzioni di hash per proteggere le password
    "admin": "a"
}


# Route per la pagina di login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Inserisci sia il nome utente che la password.', 'warning')
        else:
            # Verifica delle credenziali
            if username in credentials and credentials[username] == password:
                flash('Login effettuato con successo!', 'success')
                return redirect(url_for('map'))
            else:
                flash('Credenziali non valide. Riprova.', 'danger')
    
    return render_template('login.html')



# Carica il DataFrame con i dati dei percorsi
output_df = pd.read_csv('resources/trasporti_ottimizzati.csv')
geolocator = Nominatim(user_agent="geo_app")

# Funzione per ottenere le coordinate di una città
def get_coordinates(city):
    location = geolocator.geocode(city)
    if location:
        return [location.latitude, location.longitude]
    return None

# Prepara i dati delle rotte con ospedale di partenza, città intermedie e destinazione
routes_data = []
for _, row in output_df.iterrows():
    ospedale_partenza = row['ospedale_partenza']
    percorso = row['percorso'].strip("[]").replace("'", "").split(", ")
    destinazione = row['destinazione']
    
    # Crea la rotta completa
    complete_route = [ospedale_partenza] + percorso + [destinazione]
    coordinates = [get_coordinates(city) for city in complete_route if get_coordinates(city)]
    
    if coordinates:
        routes_data.append({'coordinates': coordinates})

@app.route('/map')
def map():
    output_df.rename(columns={
        'ospedale_partenza': 'Punto di Partenza',
        'destinazione': 'Destinazione',
        'fascia_oraria': 'Fascia Oraria',
        'percorso': 'Percorso',
        'id_pazienti': 'ID Paziente/i',
        'num_pazienti': 'Numero di Pazienti',
        'tipo_veicolo': 'Tipo di Veicolo',
        'orario_partenza': 'Orario di Partenza'
    }, inplace=True)


    table_html = output_df.to_html(classes='table table-striped', index=False)
    return render_template('map.jinja2', table_html=table_html, routes_data=routes_data)

if __name__ == "__main__":
    app.run(debug=False)
