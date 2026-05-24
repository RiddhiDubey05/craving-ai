import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet's default icon path issues
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom Animated Icons
const createEmojiIcon = (emoji, glowColor) => L.divIcon({
  html: `<div style="
    font-size: 2.5rem; 
    filter: drop-shadow(0 0 15px ${glowColor});
    animation: pulseGlow 2s infinite alternate;
  ">${emoji}</div>`,
  className: 'custom-emoji-icon',
  iconSize: [40, 40],
  iconAnchor: [20, 40]
});

// Component to dynamically pan map to follow user
function LocationController({ targetLocation }) {
  const map = useMap();
  useEffect(() => {
    if (targetLocation) {
      map.panTo(targetLocation, { animate: true, duration: 0.5 });
    }
  }, [targetLocation, map]);
  return null;
}

export default function CinematicMapEngine({ onExploreClick, navigationTarget, userPosition }) {
  const [timeOfDay, setTimeOfDay] = useState('day');
  const position = userPosition || [40.7128, -74.0060];
  const [livePosition, setLivePosition] = useState(position);
  
  useEffect(() => {
    const hour = new Date().getHours();
    if (hour >= 19 || hour < 6) {
      setTimeOfDay('night');
    } else if (hour >= 17 && hour < 19) {
      setTimeOfDay('evening');
    } else {
      setTimeOfDay('day');
    }
  }, []);

  // Sync initial live position
  useEffect(() => {
    if (!navigationTarget) {
      setLivePosition(position);
    }
  }, [position, navigationTarget]);

  // Live Navigation Animation Loop
  useEffect(() => {
    if (navigationTarget && navigationTarget.lat && navigationTarget.lon) {
      const startLat = position[0];
      const startLon = position[1];
      const endLat = navigationTarget.lat;
      const endLon = navigationTarget.lon;
      
      const durationMs = 12000; // 12 seconds to match Frog sequence
      const intervalMs = 50;
      const steps = durationMs / intervalMs;
      let currentStep = 0;

      const timer = setInterval(() => {
        currentStep++;
        const progress = currentStep / steps;
        
        // Easing function for smoother movement (ease in-out)
        const ease = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
        
        const currentLat = startLat + (endLat - startLat) * ease;
        const currentLon = startLon + (endLon - startLon) * ease;
        
        setLivePosition([currentLat, currentLon]);

        if (currentStep >= steps) {
          clearInterval(timer);
          setLivePosition([endLat, endLon]);
        }
      }, intervalMs);

      return () => clearInterval(timer);
    }
  }, [navigationTarget]);

  const isNight = timeOfDay === 'night';
  const isEvening = timeOfDay === 'evening';

  let mapFilter = 'sepia(20%) hue-rotate(-10deg) saturate(130%) brightness(105%) contrast(100%)';
  if (isEvening) mapFilter = 'sepia(50%) hue-rotate(-20deg) saturate(200%) brightness(85%) contrast(110%)';
  if (isNight) mapFilter = 'sepia(30%) hue-rotate(190deg) saturate(150%) brightness(50%) contrast(120%)';

  let overlayGradient = 'radial-gradient(circle at 50% 50%, transparent 50%, rgba(255, 245, 230, 0.7) 100%)';
  if (isEvening) overlayGradient = 'radial-gradient(circle at 50% 50%, transparent 40%, rgba(255, 120, 0, 0.3) 100%)';
  if (isNight) overlayGradient = 'radial-gradient(circle at 50% 50%, transparent 30%, rgba(10, 15, 40, 0.9) 100%)';

  const destinationCoords = navigationTarget ? [navigationTarget.lat, navigationTarget.lon] : null;

  // Calculate street lamps along the route for evening/night
  const streetLamps = [];
  if (navigationTarget && destinationCoords && (isNight || isEvening)) {
    const numLamps = 5;
    for (let i = 1; i <= numLamps; i++) {
      const frac = i / (numLamps + 1);
      const lampLat = position[0] + (destinationCoords[0] - position[0]) * frac;
      const lampLon = position[1] + (destinationCoords[1] - position[1]) * frac;
      streetLamps.push([lampLat, lampLon]);
    }
  }

  // Determine user icon emoji based on mode
  let modeEmoji = '🚶';
  if (navigationTarget?.mode === 'bike') modeEmoji = '🚴';
  if (navigationTarget?.mode === 'car') modeEmoji = '🚗';

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', borderRadius: '30px', overflow: 'hidden', boxShadow: '0 30px 60px rgba(0,0,0,0.3)' }}>
      
      <style>{`
        @keyframes pulseGlow {
          0% { transform: scale(1) translateY(0); }
          100% { transform: scale(1.1) translateY(-5px); }
        }
        .leaflet-container {
          background: ${isNight ? '#0a0f28' : '#fdf6e3'};
        }
        .leaflet-tile-pane {
          filter: ${mapFilter};
          transition: filter 2s ease;
        }
      `}</style>

      <MapContainer center={position} zoom={15} style={{ width: '100%', height: '100%' }} zoomControl={false}>
        <TileLayer
          url={isNight 
            ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            : "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          }
          attribution='&copy; OpenStreetMap contributors &copy; CARTO'
        />
        
        {/* Dynamic Pan controller follows the moving Live Position */}
        <LocationController targetLocation={livePosition} />

        {/* Cinematic Route Drawing if Navigating */}
        {navigationTarget && destinationCoords && (
          <>
            <Polyline positions={[position, destinationCoords]} color={isEvening ? "#FF4500" : "#FF7A30"} weight={5} opacity={0.8} dashArray="10, 10" className="animated-route" />
            
            {/* Render Street Lamps */}
            {streetLamps.map((lampCoords, idx) => (
              <Marker key={idx} position={lampCoords} icon={createEmojiIcon('🏮', '#FFD700')} />
            ))}

            <Marker position={destinationCoords} icon={createEmojiIcon('📍', '#FF7A30')}>
              <Popup>{navigationTarget.name}</Popup>
            </Marker>
          </>
        )}

        {/* Live User Location Marker */}
        <Marker position={livePosition} icon={createEmojiIcon(navigationTarget ? modeEmoji : '📍', '#D32F2F')}>
          <Popup>You are here.</Popup>
        </Marker>

        {/* Default Floating Pins (Only show if not navigating) */}
        {!navigationTarget && (
          <>
            <Marker position={[position[0] + 0.005, position[1] + 0.005]} icon={createEmojiIcon('🍜', '#FFD700')} />
            <Marker position={[position[0] - 0.004, position[1] - 0.008]} icon={createEmojiIcon('☕', '#FF8A65')} />
            <Marker position={[position[0] + 0.008, position[1] - 0.003]} icon={createEmojiIcon('🍰', '#FF4081')} />
          </>
        )}
        
      </MapContainer>

      {/* Atmospheric Overlays */}
      <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: overlayGradient, pointerEvents: 'none', zIndex: 400 }} />

      <motion.div 
        animate={{ x: [0, 100, 0], opacity: [0.3, 0.5, 0.3] }}
        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        style={{ position: 'absolute', top: '10%', left: '-10%', width: '120%', height: '30%', background: isNight ? 'linear-gradient(90deg, transparent, rgba(255,165,0,0.1), transparent)' : 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)', filter: 'blur(40px)', pointerEvents: 'none', zIndex: 401 }}
      />

      {/* Map HUD UI */}
      <div style={{ position: 'absolute', top: '30px', left: '30px', zIndex: 500, pointerEvents: 'auto' }}>
        <h2 style={{ fontSize: '2.5rem', margin: 0, color: isNight ? '#FFF' : '#333', textShadow: isNight ? '0 5px 15px rgba(255,165,0,0.5)' : '0 5px 15px rgba(255,255,255,0.8)' }}>
          {navigationTarget ? `Routing to ${navigationTarget.name}...` : (isNight ? 'Midnight Cravings 🌙' : 'Sunny Exploration ☀️')}
        </h2>
        {!navigationTarget && (
          <button 
            onClick={onExploreClick}
            style={{ marginTop: '15px', background: isNight ? '#FF7A30' : '#D32F2F', color: '#FFF', border: 'none', padding: '12px 25px', borderRadius: '25px', fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer', boxShadow: '0 10px 20px rgba(0,0,0,0.3)' }}
          >
            Explore Nearby Walking Routes
          </button>
        )}
      </div>

    </div>
  );
}
