import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Navigation, Bike, Car, Footprints } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix leaflet icon paths
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function ChangeView({ center, zoom }) {
  const map = useMap();
  map.setView(center, zoom);
  return null;
}

// Haversine distance formula
function getDistanceFromLatLonInKm(lat1, lon1, lat2, lon2) {
  const R = 6371; 
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

export default function ExploreNearby({ onRouteSelect, userPosition }) {
  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [navigatingPlace, setNavigatingPlace] = useState(null);
  const [mood, setMood] = useState('Anything');

  const moods = ['Anything', 'Fast Food', 'Coffee', 'Pizza', 'Biryani', 'Classy'];

  useEffect(() => {
    if (!userPosition) return;
    
    setLoading(true);
    const [lat, lon] = userPosition;
    const radius = 3000; // 3km (approx 45 min walk)
    
    let overpassFilter = `
      nwr["amenity"="restaurant"](around:${radius}, ${lat}, ${lon});
      nwr["amenity"="cafe"](around:${radius}, ${lat}, ${lon});
      nwr["amenity"="fast_food"](around:${radius}, ${lat}, ${lon});
    `;

    if (mood === 'Fast Food') {
      overpassFilter = `nwr["amenity"="fast_food"](around:${radius}, ${lat}, ${lon});`;
    } else if (mood === 'Coffee') {
      overpassFilter = `nwr["amenity"="cafe"](around:${radius}, ${lat}, ${lon});`;
    } else if (mood === 'Pizza') {
      overpassFilter = `nwr["cuisine"~"pizza|italian"](around:${radius}, ${lat}, ${lon});`;
    } else if (mood === 'Biryani') {
      overpassFilter = `nwr["cuisine"~"indian|biryani|asian"](around:${radius}, ${lat}, ${lon});`;
    } else if (mood === 'Classy') {
      overpassFilter = `nwr["amenity"="restaurant"]["cuisine"~"fine|french|italian|steak|seafood|international"](around:${radius}, ${lat}, ${lon});`;
    }

    const query = `
      [out:json];
      (
        ${overpassFilter}
      );
      out center 200;
    `;

    fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST',
      body: query
    })
    .then(res => res.json())
    .then(data => {
      const results = data.elements
        .filter(el => el.tags && el.tags.name)
        .map(el => {
          // 'way' and 'relation' have center lat/lon, 'node' has lat/lon
          const targetLat = el.lat || el.center?.lat;
          const targetLon = el.lon || el.center?.lon;
          const distKm = getDistanceFromLatLonInKm(lat, lon, targetLat, targetLon);
          return {
            id: el.id,
            name: el.tags.name,
            lat: targetLat,
            lon: targetLon,
            type: el.tags.cuisine || el.tags.amenity || mood,
            rating: (Math.random() * (5.0 - 4.0) + 4.0).toFixed(1),
            walk: Math.round(distKm * 12) + "m", // ~5km/h
            bike: Math.round(distKm * 4) + "m",  // ~15km/h
            car: Math.round(distKm * 2) + "m",   // ~30km/h in city
            img: `https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&q=80`
          };
        });
      setPlaces(results);
      setLoading(false);
    })
    .catch(err => {
      console.error(err);
      setLoading(false);
    });

  }, [userPosition, mood]);

  const handleStartNavigation = (mode) => {
    onRouteSelect({ ...navigatingPlace, mode });
    setNavigatingPlace(null);
  };

  return (
    <div style={{ padding: '60px 5%', marginTop: '50px', background: '#222', borderRadius: '40px 40px 0 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '3rem', margin: 0, color: '#FFF' }}>Explore Nearby</h2>
        <div style={{ background: '#FF7A30', color: '#FFF', padding: '5px 15px', borderRadius: '20px', fontWeight: 'bold' }}>
          {userPosition ? 'Live GPS Active' : 'Waiting for GPS...'}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '15px', overflowX: 'auto', paddingBottom: '20px', marginBottom: '20px' }}>
        {moods.map(m => (
          <button 
            key={m} 
            onClick={() => setMood(m)}
            style={{ 
              background: mood === m ? '#FF7A30' : '#2C2C2C', 
              color: '#FFF', 
              border: '1px solid ' + (mood === m ? '#FF7A30' : '#444'), 
              padding: '10px 25px', 
              borderRadius: '25px', 
              fontWeight: 'bold', 
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.2s'
            }}
          >
            {m}
          </button>
        ))}
      </div>

      {loading && <p style={{ color: '#FF7A30', fontSize: '1.2rem' }}>Scanning a 15km radius for {mood.toLowerCase()}...</p>}

      {loading && <p style={{ color: '#FF7A30', fontSize: '1.2rem' }}>Scanning a 3km radius for {mood.toLowerCase()}...</p>}

      {!loading && userPosition && (
        <div style={{ height: '600px', width: '100%', borderRadius: '30px', overflow: 'hidden', border: '2px solid #444', boxShadow: '0 20px 40px rgba(0,0,0,0.5)' }}>
          <MapContainer center={userPosition} zoom={14} style={{ height: '100%', width: '100%' }}>
            <ChangeView center={userPosition} zoom={14} />
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            />
            {/* User Location */}
            <Marker position={userPosition} icon={L.divIcon({ className: 'custom-user-marker', html: '<div style="background:#4285F4;width:20px;height:20px;border-radius:50%;border:3px solid white;box-shadow:0 0 10px rgba(66,133,244,0.8);"></div>' })}>
              <Popup>You are here!</Popup>
            </Marker>

            {/* Restaurant Pins */}
            {places.map(place => (
              <Marker 
                key={place.id} 
                position={[place.lat, place.lon]}
                eventHandlers={{
                  click: () => {
                    window.dispatchEvent(new CustomEvent('trigger-restaurant-menu', { detail: { place } }));
                  },
                }}
              >
                <Popup>
                  <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{place.name}</div>
                  <div style={{ color: '#FF7A30', textTransform: 'capitalize' }}>{place.type}</div>
                  <div style={{ color: '#888', fontSize: '0.9rem', marginTop: '5px' }}>⭐ {place.rating}</div>
                  <button 
                    onClick={() => window.dispatchEvent(new CustomEvent('trigger-restaurant-menu', { detail: { place } }))}
                    style={{ background: '#FF7A30', color: '#FFF', border: 'none', padding: '5px 10px', borderRadius: '10px', marginTop: '10px', cursor: 'pointer', width: '100%' }}
                  >
                    Open Action Hub
                  </button>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      )}
    </div>
  );
}
