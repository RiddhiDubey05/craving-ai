import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { searchDishes } from '../services/apiService';
import ImageWithLoader from './ImageWithLoader';


export default function SearchResults({ query, isVegOnly, onBack, onNavigate, onTriggerAssistant }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    searchDishes(query, isVegOnly)
      .then(data => {
        setResults(data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Search error in component:", err);
        setResults([]);
        setLoading(false);
      });
  }, [query, isVegOnly]);

  if (loading) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 50 }}
        style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9000, background: 'rgba(255, 246, 236, 0.95)', backdropFilter: 'blur(10px)', padding: '100px 5%', textAlign: 'center', overflowY: 'auto' }}
      >
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }} style={{ display: 'inline-block', fontSize: '3rem' }}>
          🍲
        </motion.div>
        <h2>Searching the city for {query}...</h2>
      </motion.div>
    );
  }

  if (results.length === 0) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 50 }}
        style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9000, background: 'rgba(255, 246, 236, 0.95)', backdropFilter: 'blur(10px)', padding: '100px 5%', textAlign: 'center', overflowY: 'auto' }}
      >
        <h2>No results found for "{query}" {isVegOnly && '(Veg Only)'}</h2>
        <button onClick={onBack} style={{ padding: '10px 20px', borderRadius: '20px', background: '#2C2C2C', color: '#FFF', cursor: 'pointer', border: 'none' }}>Go Back</button>
      </motion.div>
    );
  }

  const mainDish = results[0]; // For visual simplicity, focus on the top result

  return (
    <motion.div 
      initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 50 }}
      style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, zIndex: 9000, background: 'rgba(255, 246, 236, 0.95)', backdropFilter: 'blur(20px)', overflowY: 'auto', overflowX: 'hidden' }}
    >
      
      {/* Header */}
      <div style={{ padding: '40px 5%', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button onClick={onBack} style={{ background: '#2C2C2C', color: '#FFF', border: 'none', padding: '10px 20px', borderRadius: '20px', cursor: 'pointer', fontWeight: 'bold' }}>
          ← Back to Explore
        </button>
        <div style={{ fontWeight: 'bold', fontSize: '1.2rem', color: '#666' }}>
          Search Results for "{query}"
        </div>
      </div>

      {/* Hero Result Section */}
      <div style={{ padding: '0 5%', display: 'flex', flexWrap: 'wrap', gap: '50px', justifyContent: 'center' }}>
        
        {/* Massive Image Left */}
        <motion.div 
          initial={{ opacity: 0, x: -50 }} animate={{ opacity: 1, x: 0 }}
          style={{ flex: '1 1 400px', maxWidth: '600px', height: '500px', borderRadius: '30px', overflow: 'hidden', boxShadow: '0 30px 60px rgba(0,0,0,0.1)' }}
        >
          <ImageWithLoader src={mainDish.img} alt={mainDish.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </motion.div>

        {/* Details & Prices Right */}
        <motion.div 
          initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }}
          style={{ flex: '1 1 400px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
        >
          <div style={{ display: 'inline-block', padding: '5px 15px', background: mainDish.type === 'veg' ? '#4CAF50' : '#F44336', color: '#FFF', borderRadius: '20px', fontWeight: 'bold', marginBottom: '15px', width: 'fit-content' }}>
            {mainDish.type === 'veg' ? '🟢 Pure Veg' : '🔴 Non-Veg'}
          </div>
          <h1 style={{ fontSize: '3.5rem', margin: '0 0 20px 0', color: '#2C2C2C', lineHeight: 1.1 }}>{mainDish.name}</h1>
          <p style={{ fontSize: '1.2rem', color: '#666', marginBottom: '40px' }}>
            We've scanned the entire city to find the best options for you. Order now, navigate to the restaurant, or cook it yourself with Chef Capy!
          </p>

          {/* Price Comparison Table */}
          <div style={{ background: '#FFF', padding: '30px', borderRadius: '25px', boxShadow: '0 15px 35px rgba(0,0,0,0.05)', marginBottom: '40px' }}>
            <h3 style={{ margin: '0 0 20px 0', borderBottom: '2px solid #EEE', paddingBottom: '10px' }}>Live Price Comparison</h3>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><span style={{ fontSize: '1.5rem' }}>🔴</span> <strong>Zomato</strong></div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>₹{mainDish.zomato}</div>
              <a href={`https://www.zomato.com/search?dish=${encodeURIComponent(mainDish.name)}`} target="_blank" rel="noopener noreferrer" style={{ background: '#E23744', color: '#FFF', padding: '8px 20px', borderRadius: '15px', textDecoration: 'none', fontWeight: 'bold' }}>Order</a>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><span style={{ fontSize: '1.5rem' }}>🟠</span> <strong>Swiggy</strong></div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>₹{mainDish.swiggy}</div>
              <a href={`https://www.swiggy.com/search?query=${encodeURIComponent(mainDish.name)}`} target="_blank" rel="noopener noreferrer" style={{ background: '#FC8019', color: '#FFF', padding: '8px 20px', borderRadius: '15px', textDecoration: 'none', fontWeight: 'bold' }}>Order</a>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><span style={{ fontSize: '1.5rem' }}>🟣</span> <strong>Toing</strong> <span style={{ background: '#4CAF50', color: '#FFF', fontSize: '0.7rem', padding: '3px 8px', borderRadius: '10px' }}>Best Price</span></div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#4CAF50' }}>₹{mainDish.toing}</div>
              <button style={{ background: '#8E24AA', color: '#FFF', border: 'none', padding: '8px 20px', borderRadius: '15px', cursor: 'pointer', fontWeight: 'bold' }}>Order</button>
            </div>
          </div>

          {/* Alternative Actions */}
          <div style={{ display: 'flex', gap: '20px' }}>
            <button 
              onClick={() => onNavigate(mainDish.name)}
              style={{ flex: 1, padding: '20px', background: '#2C2C2C', color: '#FFF', border: 'none', borderRadius: '20px', fontSize: '1.2rem', fontWeight: 'bold', cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', transition: 'all 0.3s' }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-5px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <span>📍 Find Nearby</span>
              <span style={{ fontSize: '0.9rem', opacity: 0.7, fontWeight: 'normal' }}>Navigate on Map</span>
            </button>
            
            <button 
              onClick={() => onTriggerAssistant(mainDish.name)}
              style={{ flex: 1, padding: '20px', background: '#FFC857', color: '#2C2C2C', border: 'none', borderRadius: '20px', fontSize: '1.2rem', fontWeight: 'bold', cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', transition: 'all 0.3s' }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-5px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <span>👨‍🍳 Make it Now</span>
              <span style={{ fontSize: '0.9rem', opacity: 0.8, fontWeight: 'normal' }}>Learn with Chef Capy</span>
            </button>
          </div>

        </motion.div>
      </div>
    </motion.div>
  );
}
