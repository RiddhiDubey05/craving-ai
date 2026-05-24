import { motion } from 'framer-motion';

export default function CinematicCard({ item, index }) {
  const title = item.name || item.dish || 'Delicious Food';
  
  // Intelligent Cinematic Fallback Mapping
  let fallbackKeyword = 'food';
  if(title.toLowerCase().includes('burger')) fallbackKeyword = 'burger';
  else if(title.toLowerCase().includes('pizza')) fallbackKeyword = 'pizza';
  else if(title.toLowerCase().includes('biryani')) fallbackKeyword = 'biryani';
  else if(title.toLowerCase().includes('ramen') || title.toLowerCase().includes('noodle')) fallbackKeyword = 'ramen';
  else if(title.toLowerCase().includes('cake') || title.toLowerCase().includes('sweet')) fallbackKeyword = 'dessert';
  
  const imgUrl = item.image_url || `https://images.unsplash.com/featured/?${fallbackKeyword},delicious&sig=${title}`;

  const rating = item.rating ? `⭐ ${item.rating}` : '⭐ 4.5';
  const price = item.price || `₹${Math.floor(Math.random() * 300) + 150}`;
  const isVeg = item.is_vegetarian || item.is_vegan;

  return (
    <motion.div 
      className="glass-panel"
      whileHover={{ y: -15, scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      style={{
        width: '350px',
        height: '450px',
        overflow: 'hidden',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 40px rgba(0,0,0,0.15)'
      }}
    >
      <div style={{ height: '60%', width: '100%', overflow: 'hidden' }}>
        <img 
          src={imgUrl} 
          alt={title} 
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
        <div style={{
          position: 'absolute',
          top: '15px',
          left: '15px',
          background: 'rgba(255,255,255,0.9)',
          padding: '5px 12px',
          borderRadius: '20px',
          fontSize: '0.85rem',
          fontWeight: 'bold',
          color: isVeg ? '#2ecc71' : '#e74c3c'
        }}>
          {isVeg ? '🟩 Veg' : '🟥 Non-Veg'}
        </div>
      </div>
      
      <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: '800', margin: '0 0 10px 0' }}>{title}</h2>
          <div style={{ color: 'var(--text-dark)', opacity: 0.7, fontSize: '0.9rem' }}>
            {rating} • 15-20 min • 1.2 km
          </div>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>{price}</span>
          <motion.button 
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            style={{
              background: 'var(--accent-primary)',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '30px',
              fontWeight: 'bold',
              cursor: 'pointer',
              boxShadow: '0 5px 15px rgba(255,122,48,0.4)'
            }}
          >
            Order Now
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
