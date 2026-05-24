import React, { useState, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import LoginScreen from './components/LoginScreen';
import HomePage from './components/HomePage';
import ChefStoriesPage from './components/ChefStoriesPage';
import SearchResults from './components/SearchResults';
import CookChatPage from './components/CookChatPage';
import './index.css';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentRoute, setCurrentRoute] = useState('home'); // 'home', 'stories', 'search', 'cook-chat'
  const [searchQuery, setSearchQuery] = useState('');
  const [searchIsVeg, setSearchIsVeg] = useState(false);
  const [cookChatInitialMsg, setCookChatInitialMsg] = useState('');
  const [userName, setUserName] = useState('');
  const [userCity, setUserCity] = useState('');
  const [userPosition, setUserPosition] = useState(null);

  useEffect(() => {
    // 1. Get Username
    const savedName = localStorage.getItem('userName');
    if (savedName) {
      setUserName(savedName);
    } else {
      const name = prompt("Welcome to the 3D Chef Experience! What is your name?");
      if (name) {
        setUserName(name);
        localStorage.setItem('userName', name);
      } else {
        setUserName('Friend');
      }
    }

    // 2. Fetch highly accurate Location and Coordinates via geojs (Original API)
    fetch('https://get.geojs.io/v1/ip/geo.json')
      .then(res => res.json())
      .then(data => {
        if (data.city) {
          setUserCity(data.city);
        }
        // Use IP coordinates as a reliable fallback immediately so the map always works
        setUserPosition([parseFloat(data.latitude), parseFloat(data.longitude)]);
      })
      .catch(err => {
        console.error("Could not fetch city:", err);
        setUserCity('an unknown city');
      });

    // 3. Try to get ultra-precise Browser GPS, which will override the IP coordinates if accepted
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setUserPosition([pos.coords.latitude, pos.coords.longitude]),
        () => console.warn("Browser GPS denied. Falling back to IP coordinates."),
        { enableHighAccuracy: true, maximumAge: 0 }
      );
    }
  }, []);

  const handleSearch = (query, isVeg) => {
    setSearchQuery(query);
    setSearchIsVeg(isVeg);
    setCurrentRoute('search');
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
              userPosition={userPosition}
              onViewStories={() => setCurrentRoute('stories')} 
              onSearch={handleSearch} 
              onCookChat={(msg) => { setCookChatInitialMsg(msg || ''); setCurrentRoute('cook-chat'); }} 
            />
            <AnimatePresence>
              {currentRoute === 'search' && (
                <SearchResults 
                  key="search-overlay" 
                  query={searchQuery} 
                  isVegOnly={searchIsVeg}
                  onBack={() => setCurrentRoute('home')} 
                  onNavigate={(dish) => { setCurrentRoute('home'); }} 
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

    </>
  );
}
