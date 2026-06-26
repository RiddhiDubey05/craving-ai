import { useState } from 'react';
import { motion } from 'framer-motion';
import { X, MapPin, Navigation } from 'lucide-react';

const COUNTRIES = ['India', 'United States', 'United Kingdom', 'United Arab Emirates', 'Australia', 'Canada'];

const STATES_BY_COUNTRY = {
  India: ['Maharashtra', 'Delhi', 'Karnataka', 'Telangana', 'Tamil Nadu', 'West Bengal', 'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'Punjab'],
  'United States': ['California', 'New York', 'Texas', 'Florida', 'Illinois'],
  'United Kingdom': ['England', 'Scotland', 'Wales', 'Northern Ireland'],
  'United Arab Emirates': ['Dubai', 'Abu Dhabi', 'Sharjah'],
  Australia: ['New South Wales', 'Victoria', 'Queensland'],
  Canada: ['Ontario', 'British Columbia', 'Quebec']
};

const CITIES_BY_STATE = {
  Maharashtra: ['Mumbai', 'Pune', 'Nagpur', 'Nashik'],
  Delhi: ['New Delhi'],
  Karnataka: ['Bengaluru', 'Mysuru'],
  Telangana: ['Hyderabad', 'Warangal'],
  'Tamil Nadu': ['Chennai', 'Coimbatore'],
  'West Bengal': ['Kolkata', 'Howrah'],
  Gujarat: ['Ahmedabad', 'Surat'],
  Rajasthan: ['Jaipur', 'Udaipur'],
  'Uttar Pradesh': ['Lucknow', 'Noida'],
  Punjab: ['Chandigarh', 'Amritsar'],
  California: ['Los Angeles', 'San Francisco'],
  'New York': ['New York City', 'Buffalo'],
  Texas: ['Houston', 'Austin'],
  Florida: ['Miami', 'Orlando'],
  Illinois: ['Chicago'],
  England: ['London', 'Manchester'],
  Scotland: ['Edinburgh', 'Glasgow'],
  Wales: ['Cardiff'],
  'Northern Ireland': ['Belfast'],
  Dubai: ['Dubai City'],
  'Abu Dhabi': ['Abu Dhabi City'],
  Sharjah: ['Sharjah City'],
  'New South Wales': ['Sydney'],
  Victoria: ['Melbourne'],
  Queensland: ['Brisbane'],
  Ontario: ['Toronto', 'Ottawa'],
  'British Columbia': ['Vancouver'],
  Quebec: ['Montreal']
};

export default function ProfilePage(props) {
  const onClose = props.onClose;
  const onSaveLocation = props.onSaveLocation;
  const currentCity = props.currentCity;

  const [country, setCountry] = useState('India');
  const [state, setState] = useState('');
  const [city, setCity] = useState('');
  const [isLocating, setIsLocating] = useState(false);
  const [error, setError] = useState('');

  const states = STATES_BY_COUNTRY[country] || [];
  const cities = state ? (CITIES_BY_STATE[state] || []) : [];

  const handleSaveManual = () => {
    if (!city) {
      setError('Please select a city first.');
      return;
    }
    onSaveLocation({ cityName: city, countryName: country, useGps: false });
  };

  const handleUseCurrentLocation = () => {
    setError('');
    if (!('geolocation' in navigator)) {
      setError('Your browser does not support location detection.');
      return;
    }
    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      function(pos) {
        setIsLocating(false);
        onSaveLocation({
          useGps: true,
          coords: [pos.coords.latitude, pos.coords.longitude]
        });
      },
      function() {
        setIsLocating(false);
        setError('Location access denied. Please select manually instead.');
      },
      { enableHighAccuracy: true, maximumAge: 0 }
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        background: 'rgba(0,0,0,0.6)',
        backdropFilter: 'blur(8px)',
        zIndex: 5000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        style={{
          background: '#FFF',
          borderRadius: '20px',
          width: '100%',
          maxWidth: '420px',
          padding: '30px',
          position: 'relative',
          boxShadow: '0 25px 50px rgba(0,0,0,0.3)'
        }}
      >
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '20px', right: '20px', background: 'transparent', border: 'none', cursor: 'pointer', color: '#888' }}
        >
          <X size={22} />
        </button>

        <h2 style={{ margin: '0 0 5px 0', fontSize: '1.5rem', fontWeight: '800', color: '#222' }}>
          <MapPin size={20} style={{ verticalAlign: 'middle', marginRight: '8px' }} />
          Your Location
        </h2>
        <p style={{ margin: '0 0 20px 0', color: '#777', fontSize: '0.9rem' }}>
          Currently set to: <strong>{currentCity || 'Detecting...'}</strong>
        </p>

        <button
          onClick={handleUseCurrentLocation}
          disabled={isLocating}
          style={{
            width: '100%',
            padding: '14px',
            borderRadius: '12px',
            border: 'none',
            background: '#FFC857',
            color: '#B71C1C',
            fontWeight: 'bold',
            fontSize: '0.95rem',
            cursor: isLocating ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            marginBottom: '20px'
          }}
        >
          <Navigation size={18} />
          {isLocating ? 'Detecting...' : 'Use My Current Location'}
        </button>

        <div style={{ textAlign: 'center', color: '#AAA', fontSize: '0.85rem', margin: '10px 0' }}>— or choose manually —</div>

        <label style={{ fontSize: '0.85rem', fontWeight: '600', color: '#555' }}>Country</label>
        <select
          value={country}
          onChange={(e) => { setCountry(e.target.value); setState(''); setCity(''); }}
          style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #DDD', marginTop: '6px', marginBottom: '15px', fontSize: '0.95rem' }}
        >
          {COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        <label style={{ fontSize: '0.85rem', fontWeight: '600', color: '#555' }}>State</label>
        <select
          value={state}
          onChange={(e) => { setState(e.target.value); setCity(''); }}
          style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #DDD', marginTop: '6px', marginBottom: '15px', fontSize: '0.95rem' }}
        >
          <option value="">Select a state</option>
          {states.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <label style={{ fontSize: '0.85rem', fontWeight: '600', color: '#555' }}>City</label>
        <select
          value={city}
          onChange={(e) => setCity(e.target.value)}
          style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #DDD', marginTop: '6px', marginBottom: '15px', fontSize: '0.95rem' }}
        >
          <option value="">Select a city</option>
          {cities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        {error && <p style={{ color: '#D32F2F', fontSize: '0.85rem', margin: '0 0 15px 0' }}>{error}</p>}

        <button
          onClick={handleSaveManual}
          style={{
            width: '100%',
            padding: '14px',
            borderRadius: '12px',
            border: 'none',
            background: '#222',
            color: '#FFF',
            fontWeight: 'bold',
            fontSize: '0.95rem',
            cursor: 'pointer'
          }}
        >
          Save Location
        </button>
      </motion.div>
    </motion.div>
  );
}
