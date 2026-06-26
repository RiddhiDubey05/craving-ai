import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, MapPin, Star, ShoppingBag, Music, Loader2 } from 'lucide-react';
import ImageWithLoader from './ImageWithLoader';
import { getImageUrl } from '../services/apiService';
import { formatPrice } from '../utils/currency';

export default function ImmersiveCultureView(props) {
  const region = props.region;
  const userCity = props.userCity;
  const userCountry = props.userCountry;
  const onClose = props.onClose;

  const [deliveryItems, setDeliveryItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const audioRef = useRef(null);

  const cultureAssets = {
    chinese: { bg: 'https://images.unsplash.com/photo-1552611052-33e04de081de?w=1600&q=80', audio: '/chinese-tune.mp3' },
    indian: { bg: 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=1600&q=80', audio: '/indian-tune.mp3' },
    western: { bg: 'https://images.unsplash.com/photo-1600891964092-4316c288032e?w=1600&q=80', audio: '/western-tune.mp3' },
    italian: { bg: 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=1600&q=80', audio: '/italian-tune.mp3' },
    street_food: { bg: 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=1600&q=80', audio: '/streetfood-tune.mp3' },
    drinks: { bg: 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=1600&q=80', audio: '/drinks-tune.mp3', audioStartOffset: 11 }
  };

  const assets = cultureAssets[region.id] || cultureAssets.indian;

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = 0.5;
      if (assets.audioStartOffset) {
        audioRef.current.currentTime = assets.audioStartOffset;
      }
      audioRef.current.play()
        .then(() => {
          setTimeout(() => {
            let fadeInterval;
            if (audioRef.current) {
              let vol = audioRef.current.volume;
              fadeInterval = setInterval(() => {
                if (audioRef.current && vol > 0.05) {
                  vol -= 0.05;
                  audioRef.current.volume = vol;
                } else {
                  clearInterval(fadeInterval);
                  if (audioRef.current) {
                    audioRef.current.pause();
                    audioRef.current.volume = 0.5;
                  }
                }
              }, 150);
            }
          }, 4500);
        })
        .catch(e => console.log('Audio autoplay blocked', e));
    }

    const fetchDeliveryItems = async () => {
      try {
        const response = await fetch('http://localhost:3001/api/culture-delivery', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ culture: region.title, city: userCity })
        });
        const data = await response.json();

        if (data.error || !Array.isArray(data) || data.length === 0) {
          throw new Error('Failed to fetch');
        }
        setDeliveryItems(data);
      } catch (err) {
        console.error('Using fallback delivery items');
        const fx = userCountry;
        const specificFallbacks = {
          chinese: [
            { id: 1, dishName: 'Sichuan Hotpot', restaurant: 'Dragon Court', price: formatPrice(800, fx), rating: 4.9, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1582878826629-29b7ad1cb438?w=800&q=80' },
            { id: 2, dishName: 'Peking Duck', restaurant: 'Imperial Kitchen', price: formatPrice(1200, fx), rating: 4.8, platforms: ['Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1544025162-d76694265947?w=800&q=80' },
            { id: 3, dishName: 'Xiaolongbao', restaurant: 'Dumpling House', price: formatPrice(450, fx), rating: 4.7, platforms: ['Zomato', 'Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=800&q=80' },
            { id: 4, dishName: 'Dan Dan Noodles', restaurant: 'Street Wok', price: formatPrice(350, fx), rating: 4.6, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1552611052-33e04de081de?w=800&q=80' }
          ],
          indian: [
            { id: 1, dishName: 'Butter Chicken', restaurant: 'Punjab Grill', price: formatPrice(450, fx), rating: 4.8, platforms: ['Zomato', 'Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1603894584373-5ac82b6ae398?w=800&q=80' },
            { id: 2, dishName: 'Hyderabadi Biryani', restaurant: 'Paradise', price: formatPrice(350, fx), rating: 4.9, platforms: ['Zomato', 'Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1631515243349-e0cb75fb8d3a?w=800&q=80' },
            { id: 3, dishName: 'Palak Paneer', restaurant: 'Dhaba Estd 1986', price: formatPrice(300, fx), rating: 4.6, platforms: ['Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1631452180519-c014fe946bc0?w=800&q=80' },
            { id: 4, dishName: 'Masala Dosa', restaurant: 'Saravana Bhavan', price: formatPrice(200, fx), rating: 4.9, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1589301760014-d929f39ce9b1?w=800&q=80' }
          ],
          western: [
            { id: 1, dishName: 'Ribeye Steak', restaurant: 'The Smokehouse', price: formatPrice(1500, fx), rating: 4.9, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1600891964092-4316c288032e?w=800&q=80' },
            { id: 2, dishName: 'Truffle Pasta', restaurant: 'Bistro 22', price: formatPrice(650, fx), rating: 4.7, platforms: ['Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?w=800&q=80' },
            { id: 3, dishName: 'Classic Cheeseburger', restaurant: 'Burger Joint', price: formatPrice(400, fx), rating: 4.8, platforms: ['Zomato', 'Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&q=80' },
            { id: 4, dishName: 'Mac and Cheese', restaurant: 'Comfort Eats', price: formatPrice(350, fx), rating: 4.5, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1612871689353-cccf581d667b?w=800&q=80' }
          ],
          italian: [
            { id: 1, dishName: 'Margherita Pizza', restaurant: 'Napoli Oven', price: formatPrice(400, fx), rating: 4.9, platforms: ['Zomato', 'Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=800&q=80' },
            { id: 2, dishName: 'Spaghetti Carbonara', restaurant: 'Trattoria', price: formatPrice(600, fx), rating: 4.8, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1612874742237-6526221588e3?w=800&q=80' },
            { id: 3, dishName: 'Lasagna', restaurant: 'Mama Mia', price: formatPrice(500, fx), rating: 4.7, platforms: ['Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1619895092538-128341789043?w=800&q=80' },
            { id: 4, dishName: 'Tiramisu', restaurant: 'Dolce Vita', price: formatPrice(350, fx), rating: 4.9, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1571115177098-24ec42ed204d?w=800&q=80' }
          ],
          street_food: [
            { id: 1, dishName: 'Pani Puri', restaurant: 'Chaat Corner', price: formatPrice(100, fx), rating: 4.9, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1626132647523-66f5bf380027?w=800&q=80' },
            { id: 2, dishName: 'Vada Pav', restaurant: 'Mumbai Express', price: formatPrice(80, fx), rating: 4.8, platforms: ['Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=800&q=80' },
            { id: 3, dishName: 'Kathi Roll', restaurant: 'Rolls King', price: formatPrice(150, fx), rating: 4.6, platforms: ['Zomato', 'Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=800&q=80' },
            { id: 4, dishName: 'Momos', restaurant: 'Himalayan Bite', price: formatPrice(120, fx), rating: 4.7, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1625220194771-7ebdea0b70b9?w=800&q=80' }
          ],
          drinks: [
            { id: 1, dishName: 'Dark Mocha', restaurant: 'The Roastery', price: formatPrice(250, fx), rating: 4.9, platforms: ['Zomato', 'Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=800&q=80' },
            { id: 2, dishName: 'Matcha Latte', restaurant: 'Zen Cafe', price: formatPrice(280, fx), rating: 4.7, platforms: ['Swiggy'], imageUrl: 'https://images.unsplash.com/photo-1515823662972-da6a2e4d3002?w=800&q=80' },
            { id: 3, dishName: 'New York Cheesecake', restaurant: 'Bakehouse', price: formatPrice(300, fx), rating: 4.8, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=800&q=80' },
            { id: 4, dishName: 'Mango Sticky Rice', restaurant: 'Thai Sweet', price: formatPrice(250, fx), rating: 4.8, platforms: ['Zomato'], imageUrl: 'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=800&q=80' }
          ]
        };

        let rawFallback = specificFallbacks[region.id] || specificFallbacks.indian;
        setDeliveryItems(rawFallback);
      } finally {
        setLoading(false);
      }
    };

    fetchDeliveryItems();

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, [region.id, region.title, userCity, userCountry]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 1.05 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        zIndex: 9999,
        background: '#000',
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto'
      }}
    >
      <audio ref={audioRef} src={assets.audio} loop />

      <img
        src={assets.bg}
        alt={region.title}
        style={{
          position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
          objectFit: 'cover', opacity: 0.4, zIndex: 0
        }}
      />

      <div style={{
        position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
        background: 'radial-gradient(circle at center, transparent 0%, #000 100%)',
        zIndex: 1
      }} />

      <div style={{ position: 'relative', zIndex: 10, padding: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <button
          onClick={onClose}
          style={{ background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)', border: 'none', color: '#FFF', padding: '15px 25px', borderRadius: '30px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.2rem', fontWeight: 'bold' }}
        >
          <ArrowLeft size={24} /> Back
        </button>
        <div style={{ background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)', color: '#FFF', padding: '10px 20px', borderRadius: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Music size={20} /> <span style={{ opacity: 0.8 }}>Now Playing: Cultural Tunes</span>
        </div>
      </div>

      <div style={{ position: 'relative', zIndex: 10, padding: '0 50px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <h1 style={{ fontSize: '6rem', margin: 0, color: '#FFF', fontWeight: '900', textShadow: '0 10px 30px rgba(0,0,0,0.8)', letterSpacing: '2px' }}>
            {region.title}
          </h1>
          <p style={{ fontSize: '2rem', color: region.theme, margin: '10px 0 40px 0', fontWeight: 'bold', textShadow: '0 5px 15px rgba(0,0,0,0.5)' }}>
            {region.subtitle}
          </p>
        </motion.div>

        <div>
          <h3 style={{ color: '#FFF', fontSize: '1.5rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <MapPin color={region.theme} /> Local Deliveries in {userCity}
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
            <AnimatePresence>
              {loading ? (
                <div style={{ display: 'flex', gap: '10px', color: '#FFF', alignItems: 'center' }}>
                  <Loader2 className="spin" size={24} /> Curating local restaurants...
                </div>
              ) : (
                deliveryItems.map((item, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 + (idx * 0.1) }}
                    style={{
                      background: 'rgba(255,255,255,0.1)',
                      backdropFilter: 'blur(15px)',
                      border: '1px solid rgba(255,255,255,0.2)',
                      padding: '25px',
                      borderRadius: '20px',
                      color: '#FFF',
                      cursor: 'pointer',
                      transition: 'transform 0.2s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-5px)'}
                    onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                    onClick={() => window.open('https://www.zomato.com/search?q=' + encodeURIComponent(item.dishName + ' ' + item.restaurant), '_blank')}
                  >
                    <div style={{ width: '100%', height: '150px', marginBottom: '15px', borderRadius: '15px', overflow: 'hidden' }}>
                      <ImageWithLoader src={item.imageUrl || getImageUrl(item.dishName)} alt={item.dishName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                      <h4 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 'bold' }}>{item.dishName}</h4>
                      <span style={{ background: region.theme, padding: '5px 10px', borderRadius: '15px', fontWeight: 'bold' }}>
                        {item.price}
                      </span>
                    </div>
                    <p style={{ margin: '0 0 15px 0', opacity: 0.8, fontSize: '1.1rem' }}>by {item.restaurant}</p>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#FFD700' }}>
                        <Star size={18} fill="#FFD700" /> {item.rating}
                      </div>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        {item.platforms.map((p, i) => (
                          <span key={i} style={{ fontSize: '0.8rem', background: 'rgba(255,255,255,0.2)', padding: '4px 8px', borderRadius: '10px' }}>{p}</span>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
