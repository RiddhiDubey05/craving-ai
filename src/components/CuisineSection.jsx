import { motion } from 'framer-motion';

const dishes = [
  { id: 1, name: "Spicy Sichuan Noodles", desc: "Authentic heat from the heart of Sichuan.", price: "₹250", img: "https://images.unsplash.com/photo-1552611052-33e04de081de?w=600&q=80" },
  { id: 2, name: "Dim Sum Basket", desc: "Steamed to perfection with traditional recipes.", price: "₹300", img: "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=600&q=80" },
  { id: 3, name: "Peking Duck", desc: "Crispy, savory, and rich in history.", price: "₹600", img: "https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80" }
];

export default function CuisineSection({ title, subtitle, themeColor }) {
  return (
    <div style={{
      width: '100%',
      padding: '80px 5%',
      background: '#FFF6EC', // Warm beige background
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center'
    }}>
      
      {/* Section Header */}
      <div style={{ textAlign: 'center', marginBottom: '50px' }}>
        <h2 style={{ fontSize: '3rem', color: themeColor || '#B71C1C', fontWeight: '900', fontFamily: 'serif', margin: 0 }}>
          {title}
        </h2>
        <p style={{ fontSize: '1.2rem', color: '#666', marginTop: '10px', fontStyle: 'italic' }}>
          {subtitle}
        </p>
      </div>

      {/* 3-Card Layout */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '40px',
        width: '100%',
        maxWidth: '1200px'
      }}>
        {dishes.map((dish, i) => (
          <motion.div
            key={dish.id}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ delay: i * 0.2, duration: 0.6 }}
            whileHover={{ y: -10 }}
            style={{
              background: '#FFF',
              borderRadius: '24px',
              overflow: 'hidden',
              boxShadow: '0 15px 35px rgba(0,0,0,0.05)',
              display: 'flex',
              flexDirection: 'column',
              cursor: 'pointer',
              border: `2px solid ${themeColor || '#B71C1C'}20`
            }}
          >
            <div style={{ height: '250px', overflow: 'hidden' }}>
              <motion.img 
                whileHover={{ scale: 1.1 }}
                transition={{ duration: 0.4 }}
                src={dish.img} 
                alt={dish.name}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            </div>
            
            <div style={{ padding: '25px', display: 'flex', flexDirection: 'column', flex: 1 }}>
              <h3 style={{ fontSize: '1.5rem', color: '#2C2C2C', margin: '0 0 10px 0', fontWeight: '800' }}>{dish.name}</h3>
              <p style={{ color: '#666', flex: 1, margin: '0 0 20px 0', lineHeight: 1.5 }}>{dish.desc}</p>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '1.3rem', fontWeight: 'bold', color: themeColor || '#B71C1C' }}>{dish.price}</span>
                <button style={{
                  background: themeColor || '#B71C1C',
                  color: 'white',
                  border: 'none',
                  padding: '10px 20px',
                  borderRadius: '20px',
                  fontWeight: 'bold',
                  cursor: 'pointer'
                }}>
                  Explore
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

    </div>
  );
}
