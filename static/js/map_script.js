// Inizializza la mappa
var map = L.map('map').setView([46.4983, 11.3548], 10);  // Posizione di default centrata su Bolzano

// Aggiungi un layer di base da OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Dati dei percorsi passati dal backend
var routes = {{ routes_data|tojson }};

// Colori predefiniti per i percorsi
var colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightblue', 'lightgreen', 'gray'];

// Funzione per aggiungere i percorsi alla mappa
routes.forEach(function(route, index) {
    var latlngs = route.coordinates.map(function(coord) {
        return [coord[0], coord[1]];  // Converti le coordinate in formato LatLng
    });

    // Aggiungi la polyline per ogni percorso
    L.polyline(latlngs, {
        color: colors[index % colors.length],
        weight: 5,
        opacity: 0.7
    }).addTo(map).bindPopup('Percorso ' + (index + 1));
});