import { useState } from 'react';
import { Search, Utensils, Navigation } from 'lucide-react';
import { motion } from 'framer-motion';

export default function MassiveSearch({ onSearch, onSubmitSearch }) {
  const [query, setQuery] = useState('');
  const [isVegOnly, setIsVegOnly] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && onSearch) {
      onSearch(query.trim(), isVegOnly);
      if (onSubmitSearch) onSubmitSearch();
    }
  };

  return (
    <div style={{ padding: '0 5%', marginTop: '-80px', position: 'relative', zIndex: 100, display: 'flex', justifyContent: 'center' }}>
      <motion.form 
        onSubmit={handleSubmit}
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
        style={{ 
          background: 'rgba(30, 30, 30, 0.6)', 
          backdropFilter: 'blur(30px)', 
          padding: '15px 25px', 
          borderRadius: '30px', 
          boxShadow: '0 20px 40px rgba(0,0,0,0.5)', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '15px', 
          width: '100%',
          maxWidth: '800px', 
          border: '1px solid rgba(255,122,48,0.3)' 
        }}
      >
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <div style={{ background: 'linear-gradient(135deg, #FF7A30, #D32F2F)', borderRadius: '50%', width: '45px', height: '45px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#FFF', flexShrink: 0, boxShadow: '0 10px 20px rgba(211,47,47,0.4)' }}>
            <Search size={20} />
          </div>
          <input 
            type="text" 
            placeholder="Search the culinary universe (e.g. Spicy noodles)..." 
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (onSearch) onSearch(e.target.value, isVegOnly);
            }}
            style={{ flex: 1, border: 'none', fontSize: '1.3rem', outline: 'none', background: 'transparent', color: '#FFF', fontWeight: 'bold' }}
          />
          <button type="submit" style={{ background: '#FFF', color: '#1A1A1A', border: 'none', padding: '12px 30px', borderRadius: '25px', fontSize: '1.1rem', fontWeight: '900', cursor: 'pointer', transition: 'transform 0.2s', boxShadow: '0 10px 20px rgba(0,0,0,0.2)' }} onMouseOver={e => e.currentTarget.style.transform = 'scale(1.05)'} onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}>
            Explore
          </button>
        </div>

        {/* Veg / Non-Veg Filter & Quick Tags */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingLeft: '80px' }}>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <button 
              type="button"
              onClick={() => setIsVegOnly(!isVegOnly)}
              style={{
                background: isVegOnly ? 'rgba(76, 175, 80, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                color: isVegOnly ? '#4CAF50' : '#CCC',
                border: isVegOnly ? '1px solid #4CAF50' : '1px solid #555',
                padding: '10px 20px',
                borderRadius: '20px',
                fontWeight: 'bold',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.3s'
              }}
            >
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: isVegOnly ? '#4CAF50' : '#888' }} />
              {isVegOnly ? 'Pure Veg Enabled' : 'Show All Types'}
            </button>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <span style={{ color: '#888', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.9rem' }}><Navigation size={16} /> Near You</span>
            <span style={{ color: '#888', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.9rem' }}><Utensils size={16} /> Trending</span>
          </div>

        </div>
      </motion.form>
    </div>
  );
}
