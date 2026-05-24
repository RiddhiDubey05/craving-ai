import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { getImageUrl } from '../services/apiService';
import ImageWithLoader from './ImageWithLoader';


export default function TrendingFoods({ userCity, onCookChat }) {
  const [trending, setTrending] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchTrending = async () => {
      try {
        const res = await fetch('http://localhost:3001/api/trending', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ city: userCity })
        });
        const data = await res.json();
        setTrending(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error(err);
        setTrending([]);
      } finally {
        setIsLoading(false);
      }
    };

    if (userCity !== undefined) {
      fetchTrending();
    }
  }, [userCity]);

  const handleMakeItNow = (dishName) => {
    if (onCookChat) {
      onCookChat(`I want to make ${dishName} at home. What ingredients do I need?`);
    } else {
      const event = new CustomEvent('trigger-recipe', { detail: { dish: dishName } });
      window.dispatchEvent(event);
    }
  };

  // Using imported getImageUrl from apiService


  return (
    <div style={{ padding: '60px 5%', background: '#FFF6EC' }}>
      <h2 style={{ fontSize: '2.5rem', color: '#2C2C2C', marginBottom: '30px', fontWeight: '900' }}>
        🔥 Trending Near You {userCity ? `in ${userCity}` : ''}
      </h2>
      
      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '50px', color: '#FF7A30' }}>
          <Loader2 size={40} style={{ animation: 'spin 1s linear infinite' }} />
        </div>
      ) : (
        <div style={{ display: 'flex', gap: '30px', overflowX: 'auto', paddingBottom: '20px' }}>
          {trending.map((item, i) => {
            const platform = item.platforms && item.platforms.length > 0 ? item.platforms[0] : 'Zomato';
            const platformColor = platform.toLowerCase().includes('zomato') ? '#E23744' : '#FF7A30';

            return (
              <motion.div
                key={item.id || i}
                initial={{ opacity: 0, x: 50 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                style={{
                  minWidth: '350px',
                  background: '#FFF',
                  borderRadius: '24px',
                  overflow: 'hidden',
                  boxShadow: '0 15px 35px rgba(0,0,0,0.05)',
                  border: `2px solid ${platformColor}30`,
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <div style={{ height: '200px', position: 'relative' }}>
                  <ImageWithLoader src={getImageUrl(item.dishName)} alt={item.dishName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  <div style={{ position: 'absolute', top: '15px', left: '15px', background: platformColor, color: '#FFF', padding: '5px 15px', borderRadius: '20px', fontWeight: 'bold', fontSize: '0.8rem' }}>
                    {platform}
                  </div>
                  <div style={{ position: 'absolute', bottom: '15px', right: '15px', background: '#FFF', color: '#333', padding: '5px 10px', borderRadius: '10px', fontWeight: 'bold', fontSize: '0.9rem', boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }}>
                    ⭐ {item.rating}
                  </div>
                </div>
                <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', flex: 1 }}>
                  <h3 style={{ margin: '0 0 5px 0', fontSize: '1.4rem' }}>{item.dishName}</h3>
                  <p style={{ margin: '0 0 10px 0', color: '#888', fontSize: '0.9rem' }}>{item.restaurant}</p>
                  <p style={{ fontWeight: 'bold', fontSize: '1.2rem', color: '#2C2C2C', marginBottom: '20px' }}>{item.price}</p>
                  
                  <div style={{ display: 'flex', gap: '10px', marginTop: 'auto' }}>
                    <a 
                      href={`https://www.google.com/search?q=Order+${item.dishName}+${item.restaurant}+${userCity}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ flex: 1, background: '#2C2C2C', color: '#FFF', border: 'none', padding: '12px', borderRadius: '15px', fontWeight: 'bold', cursor: 'pointer', textAlign: 'center', textDecoration: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      Order
                    </a>
                    <button 
                      onClick={() => handleMakeItNow(item.dishName)}
                      style={{ flex: 1, background: 'transparent', color: '#FF7A30', border: '2px solid #FF7A30', padding: '12px', borderRadius: '15px', fontWeight: 'bold', cursor: 'pointer' }}
                    >
                      Make it Now
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
