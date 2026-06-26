import React, { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import LoginScreen from './components/LoginScreen';
import HomePage from './components/HomePage';
import ChefStoriesPage from './components/ChefStoriesPage';
import SearchResults from './components/SearchResults';
import CookChatPage from './components/CookChatPage';
import ProfilePage from './components/ProfilePage';
import './index.css';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentRoute, setCurrentRoute] = useState('home');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchIsVeg, setSearchIsVeg] = useState(false);
  const [cookChatInitialMsg, setCookChatInitialMsg] = useState('');
  const [userName, setUserName] = useState('');
  const [userCity, setUserCity] = useState('');
  const [userCountry, setUserCountry] = useState('India');
  const [userPosition, setUserPosition] = useState(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  useEffect(() => {
    const savedName = localStorage.getItem('userName');
    if (savedName) {
      setUserName(savedName);
    } else {
      const name = prompt('Welcome to the 3D Chef Experience! What is your name?');
      if (name) {
        setUserName(name);
        localStorage.setItem('userName', name);
      } else {
        setUserName('Friend');
      }
    }

    const savedCity = localStorage.getItem('userCity');
    const savedCountry = localStorage.getItem('userCountry');
    const savedLat = localStorage.getItem('userLat');
    const savedLng = localStorage.getItem('userLng');
    if (savedCity && savedLat && savedLng) {
      setUserCity(savedCity);
      if (savedCountry) { setUserCountry(savedCountry); }
      setUserPosition([parseFloat(savedLat), parseFloat(savedLng)]);
      return;
    }

    fetch('https://get.geojs.io/v1/ip/geo.json')
      .then(function(res) { return res.json(); })
      .then(function(data) {
        if (data.city) {
          setUserCity(data.city);
        }
        if (data.country) {
          setUserCountry(data.country);
        }
        setUserPosition([parseFloat(data.latitude), parseFloat(data.longitude)]);
      })
      .catch(function(err) {
        console.error('Could not fetch city:', err);
        setUserCity('an unknown city');
      });

    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        function(pos) { setUserPosition([pos.coords.latitude, pos.coords.longitude]); },
        function() { console.warn('Browser GPS denied. Falling back to IP coordinates.'); },
        { enableHighAccuracy: true, maximumAge: 0 }
      );
    }
  }, []);

  const handleSearch = (query, isVeg) => {
    setSearchQuery(query);
    setSearchIsVeg(isVeg);
    setCurrentRoute('search');
  };

  const handleSaveLocation = async (locationData) => {
    const cityName = locationData.cityName;
    const countryName = locationData.countryName;
    const useGps = locationData.useGps;
    const coords = locationData.coords;

    if (useGps && coords) {
      setUserPosition(coords);
      setUserCity('Current Location');
      localStorage.setItem('userCity', 'Current Location');
      localStorage.setItem('userLat', coords[0]);
      localStorage.setItem('userLng', coords[1]);
      setIsProfileOpen(false);
      return;
    }

    if (cityName) {
      if (countryName) {
        setUserCountry(countryName);
        localStorage.setItem('userCountry', countryName);
      }
      try {
        const res = await fetch('https://nominatim.openstreetmap.org/search?format=json&q=' + encodeURIComponent(cityName) + '&limit=1');
        const data = await res.json();
        if (data && data.length > 0) {
          const lat = parseFloat(data[0].lat);
          const lng = parseFloat(data[0].lon);
          setUserPosition([lat, lng]);
          setUserCity(cityName);
          localStorage.setItem('userCity', cityName);
          localStorage.setItem('userLat', lat);
          localStorage.setItem('userLng', lng);
        } else {
          setUserCity(cityName);
        }
      } catch (err) {
        console.error('Geocoding failed:', err);
        setUserCity(cityName);
      }
      setIsProfileOpen(false);
    }
  };

  return (
    <>
      <AnimatePresence mode="wait">
        {!isAuthenticated ? (
          <LoginScreen key="login" onLogin={() => setIsAuthenticated(true)} />
        ) : currentRoute === 'home' || currentRoute === 'search' ? (
          <div key="home-container">
            <HomePage
              userCity={userCity}
              userCountry={userCountry}
              userPosition={userPosition}
              onViewStories={() => setCurrentRoute('stories')}
              onSearch={handleSearch}
              onCookChat={(msg) => { setCookChatInitialMsg(msg || ''); setCurrentRoute('cook-chat'); }}
              onOpenProfile={() => setIsProfileOpen(true)}
            />
            <AnimatePresence>
              {currentRoute === 'search' && (
                <SearchResults
                  key="search-overlay"
                  query={searchQuery}
                  isVegOnly={searchIsVeg}
                  userCountry={userCountry}
                  onBack={() => setCurrentRoute('home')}
                  onNavigate={() => { setCurrentRoute('home'); }}
                  onTriggerAssistant={(dish) => { setCookChatInitialMsg(dish); setCurrentRoute('cook-chat'); }}
                />
              )}
            </AnimatePresence>
          </div>
        ) : currentRoute === 'stories' ? (
          <ChefStoriesPage key="stories" onBack={() => setCurrentRoute('home')} />
        ) : (
          <CookChatPage key="cook-chat" initialMessage={cookChatInitialMsg} userName={userName} onBack={() => { setCurrentRoute('home'); setCookChatInitialMsg(''); }} />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {isProfileOpen && (
          <ProfilePage
            key="profile-overlay"
            currentCity={userCity}
            onClose={() => setIsProfileOpen(false)}
            onSaveLocation={handleSaveLocation}
          />
        )}
      </AnimatePresence>
    </>
  );
}
