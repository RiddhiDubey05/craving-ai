import { motion } from 'framer-motion';

export default function FoodDetailsPanel({ food, onClose }) {
  return (
    <motion.div
      initial={{ x: '100%', opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: '100%', opacity: 0 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        width: '350px',
        background: 'rgba(255, 255, 255, 0.85)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRadius: '30px',
        padding: '25px',
        zIndex: 20,
        boxShadow: '0 20px 50px rgba(0,0,0,0.2)',
        border: '1px solid rgba(255,255,255,0.5)',
        color: '#2C2C2C'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '800' }}>{food.name}</h3>
        <button 
          onClick={onClose} 
          style={{ background: '#FF5A4E', color: '#FFF', border: 'none', borderRadius: '50%', width: '30px', height: '30px', cursor: 'pointer', fontWeight: 'bold' }}
        >
          ✕
        </button>
      </div>

      <div style={{ width: '100%', height: '150px', borderRadius: '20px', overflow: 'hidden', marginBottom: '20px' }}>
        <img src="https://images.unsplash.com/photo-1552611052-33e04de081de?w=600&q=80" alt={food.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </div>

      <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '20px' }}>
        Found nearby. Beautifully crafted, authentic flavors. ⭐ {food.rating}
      </p>

      {/* Comparison Layout */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        
        {/* Zomato Mock */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#FFF', padding: '15px', borderRadius: '15px', boxShadow: '0 4px 10px rgba(0,0,0,0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '24px', height: '24px', background: '#E23744', borderRadius: '5px', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.8rem' }}>Z</div>
            <span style={{ fontWeight: 'bold' }}>Zomato</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <span style={{ fontWeight: '800', fontSize: '1.2rem' }}>{food.priceZomato}</span>
            <button style={{ background: '#E23744', color: '#FFF', border: 'none', padding: '8px 15px', borderRadius: '15px', fontWeight: 'bold', cursor: 'pointer' }}>Order</button>
          </div>
        </div>

        {/* Swiggy Mock */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#FFF', padding: '15px', borderRadius: '15px', boxShadow: '0 4px 10px rgba(0,0,0,0.05)', border: '2px solid #FF7A30' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '24px', height: '24px', background: '#FC8019', borderRadius: '5px', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.8rem' }}>S</div>
            <span style={{ fontWeight: 'bold' }}>Swiggy</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <span style={{ fontWeight: '800', fontSize: '1.2rem', color: '#FC8019' }}>{food.priceSwiggy}</span>
            <button style={{ background: '#FF7A30', color: '#FFF', border: 'none', padding: '8px 15px', borderRadius: '15px', fontWeight: 'bold', cursor: 'pointer' }}>Best Deal</button>
          </div>
        </div>

      </div>
    </motion.div>
  );
}
