import { motion } from 'framer-motion';

export default function ThematicHero() {
  return (
    <div style={{
      position: 'relative',
      width: '100vw',
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #D32F2F 0%, #9A0007 100%)', // Deep cinematic red
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden',
      paddingTop: '80px' // offset for header
    }}>
      
      {/* Floating Quote */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 1 }}
        style={{
          position: 'absolute',
          top: '20%',
          left: '10%',
          color: '#FFF',
          fontFamily: 'serif',
          maxWidth: '400px',
          zIndex: 10
        }}
      >
        <h1 style={{ fontSize: '3.5rem', fontWeight: '900', lineHeight: '1.1', marginBottom: '10px' }}>
          Taste the <br/><span style={{ color: '#FFC857' }}>Culture.</span>
        </h1>
        <p style={{ fontSize: '1.2rem', opacity: 0.9, letterSpacing: '1px' }}>
          Every dish is a journey. Let CravingAI be your guide.
        </p>
      </motion.div>

      {/* Massive Floating Food Visual (Asian Noodles) */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 1.5, type: 'spring' }}
        style={{ position: 'relative', zIndex: 5, marginTop: '10vh' }}
      >
        {/* Glow */}
        <div style={{
          position: 'absolute',
          top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          width: '400px', height: '400px',
          background: '#FF7A30', filter: 'blur(100px)', opacity: 0.6,
          zIndex: -1
        }} />
        
        <motion.img 
          src="https://images.unsplash.com/photo-1552611052-33e04de081de?w=800&q=80" // High quality ramen/noodle bowl
          alt="Floating Noodles"
          animate={{ y: [0, -25, 0] }}
          transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
          style={{
            width: '600px',
            maxWidth: '90vw',
            borderRadius: '50%',
            boxShadow: '0 30px 60px rgba(0,0,0,0.5)',
            border: '8px solid #FFF',
            objectFit: 'cover',
            aspectRatio: '1/1'
          }}
        />
        
        {/* Floating elements mimicking chopsticks/ingredients */}
        <motion.div
          animate={{ y: [0, 15, 0], rotate: [0, 5, 0] }}
          transition={{ repeat: Infinity, duration: 4, ease: "easeInOut", delay: 1 }}
          style={{
            position: 'absolute', top: '10%', right: '-10%',
            background: '#FFC857', color: '#B71C1C',
            padding: '10px 20px', borderRadius: '30px', fontWeight: 'bold', fontSize: '1.2rem',
            boxShadow: '0 10px 20px rgba(0,0,0,0.3)'
          }}
        >
          🍜 Authentic
        </motion.div>
      </motion.div>

      {/* The Wavy / Torn Paper Edge at the bottom */}
      <div style={{ position: 'absolute', bottom: -2, left: 0, width: '100%', zIndex: 20 }}>
        <svg viewBox="0 0 1440 320" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ display: 'block', width: '100%', height: 'auto' }}>
          {/* The wave fill color matches the background of the next section (#FFF6EC) */}
          <path fill="#FFF6EC" d="M0,192L48,197.3C96,203,192,213,288,197.3C384,181,480,139,576,144C672,149,768,203,864,224C960,245,1056,235,1152,213.3C1248,192,1344,160,1392,144L1440,128L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path>
        </svg>
      </div>

    </div>
  );
}
