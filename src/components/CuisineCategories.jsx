import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ImmersiveCultureView from './ImmersiveCultureView';

const regions = [
  {
    id: 'chinese',
    title: "Journey to the East",
    subtitle: "Authentic Chinese",
    img: "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600&q=80",
    theme: "#D32F2F"
  },
  {
    id: 'indian',
    title: "The Spice Route",
    subtitle: "Vibrant Indian Heritage",
    img: "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&q=80",
    theme: "#FF7A30"
  },
  {
    id: 'western',
    title: "Western Comfort",
    subtitle: "Rustic European & American",
    img: "https://images.unsplash.com/photo-1600891964092-4316c288032e?w=600&q=80",
    theme: "#F8E9A1"
  },
  {
    id: 'italian',
    title: "Rustic Italian",
    subtitle: "Wood-fired & Passionate",
    img: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&q=80",
    theme: "#3E2723"
  },
  {
    id: 'street_food',
    title: "Street Food",
    subtitle: "Bustling Local Flavors",
    img: "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600&q=80",
    theme: "#FFB300"
  },
  {
    id: 'drinks',
    title: "Drinks & Desserts",
    subtitle: "Sweet Tooth & Beverages",
    img: "https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=600&q=80",
    theme: "#4A3026"
  }
];

export default function CuisineCategories(props) {
  const userCity = props.userCity;
  const userCountry = props.userCountry;
  const onCookChat = props.onCookChat;

  const [selectedRegion, setSelectedRegion] = useState(null);

  return (
    <div id="cuisine-categories" style={{ padding: '40px 5%', background: 'transparent' }}>
      <h2 style={{ fontSize: '2.5rem', color: '#2C2C2C', marginBottom: '30px', fontWeight: '900' }}>
        Explore Cultures
      </h2>

      <div style={{ display: 'flex', gap: '30px', overflowX: 'auto', paddingBottom: '20px' }}>
        {regions.map((region, i) => (
          <motion.div
            key={region.id}
            onClick={() => setSelectedRegion(region)}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
            whileHover={{ y: -10, cursor: 'pointer' }}
            style={{
              minWidth: '300px', height: '400px', borderRadius: '24px', overflow: 'hidden', position: 'relative', boxShadow: '0 15px 35px rgba(0,0,0,0.1)'
            }}
          >
            <img src={region.img} alt={region.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', padding: '30px 20px', background: 'linear-gradient(to top, rgba(0,0,0,0.9), transparent)' }}>
              <h3 style={{ color: '#FFF', fontSize: '1.8rem', margin: '0 0 5px 0' }}>{region.title}</h3>
              <p style={{ color: region.theme, fontWeight: 'bold', margin: 0 }}>{region.subtitle}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <AnimatePresence>
        {selectedRegion && (
          <ImmersiveCultureView
            region={selectedRegion}
            userCity={userCity}
            userCountry={userCountry}
            onClose={() => setSelectedRegion(null)}
            onCookChat={onCookChat}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
