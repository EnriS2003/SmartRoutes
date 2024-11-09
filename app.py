from flask import Flask, render_template
import pandas as pd
from geopy.geocoders import Nominatim

app = Flask(__name__)

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

@app.route('/')
def display_output():
    table_html = output_df.to_html(classes='table table-striped', index=False)
    return render_template('map.jinja2', table_html=table_html, routes_data=routes_data)

if __name__ == "__main__":
    app.run(debug=True)
