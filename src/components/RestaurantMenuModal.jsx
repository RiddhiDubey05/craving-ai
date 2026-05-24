import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MapPin, Navigation, Star } from 'lucide-react';

export default function RestaurantMenuModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [place, setPlace] = useState(null);

  useEffect(() => {
    const handleTrigger = (e) => {
      setPlace(e.detail.place);
      setIsOpen(true);
    };
    window.addEventListener('trigger-restaurant-menu', handleTrigger);
    return () => window.removeEventListener('trigger-restaurant-menu', handleTrigger);
  }, []);

  if (!isOpen || !place) return null;

  // Mock a menu based on the place type or name
  const mockMenu = [
    { name: `Signature ${place.type || 'Special'}`, price: '₹450', desc: 'Our chef’s highly recommended local favorite.' },
    { name: 'House Appetizer Platter', price: '₹350', desc: 'A perfect start with assorted regional bites.' },
    { name: 'Classic Main Course', price: '₹550', desc: 'Authentic flavors cooked to perfection.' },
    { name: 'Fresh Salad Bowl', price: '₹280', desc: 'Crisp, organic greens with house dressing.' },
    { name: 'Decadent Dessert', price: '₹250', desc: 'A sweet finish to your culinary journey.' }
  ];

  const handleOpenMaps = () => {
    window.open(`https://www.google.com/maps/dir/?api=1&destination=${place.lat},${place.lon}`, '_blank');
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(15px)',
          zIndex: 99999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
        }}
      >
        <motion.div
          initial={{ scale: 0.9, y: 50 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 50 }}
          style={{
            background: '#FFF', borderRadius: '30px', overflow: 'hidden',
            maxWidth: '600px', width: '100%', position: 'relative',
            boxShadow: '0 30px 60px rgba(0,0,0,0.5)', maxHeight: '90vh', display: 'flex', flexDirection: 'column'
          }}
        >
          {/* Header Image */}
          <div style={{ height: '200px', position: 'relative' }}>
            <img src={place.img} alt={place.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'linear-gradient(to bottom, rgba(0,0,0,0.6), transparent, rgba(0,0,0,0.8))' }} />
            
            <button 
              onClick={() => setIsOpen(false)}
              style={{ position: 'absolute', top: '20px', right: '20px', background: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(10px)', border: 'none', cursor: 'pointer', color: '#FFF', borderRadius: '50%', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            >
              <X size={24} />
            </button>
            
            <div style={{ position: 'absolute', bottom: '20px', left: '20px', color: '#FFF' }}>
              <h2 style={{ fontSize: '2.5rem', margin: '0 0 5px 0', textShadow: '0 2px 10px rgba(0,0,0,0.5)' }}>{place.name}</h2>
              <div style={{ display: 'flex', gap: '15px', alignItems: 'center', fontWeight: 'bold' }}>
                <span style={{ color: '#FFD700', display: 'flex', alignItems: 'center', gap: '5px' }}><Star size={18} fill="#FFD700" /> {place.rating}</span>
                <span style={{ textTransform: 'capitalize', background: 'rgba(255,122,48,0.8)', padding: '2px 10px', borderRadius: '15px' }}>{place.type}</span>
              </div>
            </div>
          </div>

          {/* Logistics Action Buttons */}
          <div style={{ padding: '30px', flex: 1, background: '#F8F9FA', display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <h3 style={{ fontSize: '1.5rem', color: '#333', marginBottom: '10px' }}>
              Action Hub
            </h3>
            
            <button 
              onClick={handleOpenMaps}
              style={{ width: '100%', background: '#4285F4', color: '#FFF', border: 'none', padding: '15px', borderRadius: '15px', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', transition: 'transform 0.2s' }}
              onMouseOver={e => e.currentTarget.style.transform = 'scale(1.02)'}
              onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              <Navigation size={20} /> Get Directions on Google Maps
            </button>

            <button 
              onClick={() => window.open(`https://m.uber.com/ul/?action=setPickup&dropoff[latitude]=${place.lat}&dropoff[longitude]=${place.lon}`, '_blank')}
              style={{ width: '100%', background: '#000', color: '#FFF', border: 'none', padding: '15px', borderRadius: '15px', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', transition: 'transform 0.2s' }}
              onMouseOver={e => e.currentTarget.style.transform = 'scale(1.02)'}
              onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              🚗 Book an Uber Here
            </button>

            <button 
              onClick={() => window.open(`https://www.zomato.com/search?q=${place.name}`, '_blank')}
              style={{ width: '100%', background: '#E23744', color: '#FFF', border: 'none', padding: '15px', borderRadius: '15px', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', transition: 'transform 0.2s' }}
              onMouseOver={e => e.currentTarget.style.transform = 'scale(1.02)'}
              onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              View Menu on Zomato
            </button>

            <button 
              onClick={() => window.open(`https://www.swiggy.com/search?q=${place.name}`, '_blank')}
              style={{ width: '100%', background: '#FC8019', color: '#FFF', border: 'none', padding: '15px', borderRadius: '15px', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', transition: 'transform 0.2s' }}
              onMouseOver={e => e.currentTarget.style.transform = 'scale(1.02)'}
              onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              View Menu on Swiggy
            </button>
          </div>

          {/* Map Redirect Footer */}
          <div style={{ padding: '15px', background: '#FFF', borderTop: '1px solid #EEE', textAlign: 'center', color: '#888', fontSize: '0.9rem' }}>
            GPS Coordinates: {place.lat.toFixed(4)}, {place.lon.toFixed(4)}
          </div>

        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
