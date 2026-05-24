import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Clock, Users, ChefHat } from 'lucide-react';

export default function RecipeModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [dishName, setDishName] = useState('');

  useEffect(() => {
    const handleTrigger = (e) => {
      setDishName(e.detail.dish);
      setIsOpen(true);
    };
    window.addEventListener('trigger-recipe', handleTrigger);
    return () => window.removeEventListener('trigger-recipe', handleTrigger);
  }, []);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
          background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(10px)',
          zIndex: 99999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
        }}
      >
        <motion.div
          initial={{ scale: 0.9, y: 50 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 50 }}
          style={{
            background: '#FFF6EC', borderRadius: '30px', padding: '40px',
            maxWidth: '600px', width: '100%', position: 'relative',
            boxShadow: '0 20px 50px rgba(0,0,0,0.5)', maxHeight: '90vh', overflowY: 'auto'
          }}
        >
          <button 
            onClick={() => setIsOpen(false)}
            style={{ position: 'absolute', top: '20px', right: '20px', background: 'transparent', border: 'none', cursor: 'pointer', color: '#333' }}
          >
            <X size={32} />
          </button>

          <h2 style={{ fontSize: '2.5rem', color: '#D32F2F', marginTop: 0, marginBottom: '10px' }}>
            {dishName}
          </h2>
          <p style={{ fontSize: '1.2rem', color: '#555', marginBottom: '30px' }}>Let's cook this masterpiece together!</p>

          <div style={{ display: 'flex', gap: '20px', marginBottom: '30px', borderBottom: '2px solid rgba(0,0,0,0.1)', paddingBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#FF7A30', fontWeight: 'bold' }}>
              <Clock size={20} /> 45 mins
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#FF7A30', fontWeight: 'bold' }}>
              <Users size={20} /> Serves 2
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#FF7A30', fontWeight: 'bold' }}>
              <ChefHat size={20} /> Medium Difficulty
            </div>
          </div>

          <h3 style={{ fontSize: '1.5rem', color: '#333', marginBottom: '15px' }}>Ingredients</h3>
          <ul style={{ fontSize: '1.1rem', color: '#444', lineHeight: '1.8', marginBottom: '30px', paddingLeft: '20px' }}>
            <li>Fresh local produce (specific to {dishName})</li>
            <li>Premium spices & seasoning</li>
            <li>High-quality cooking oil or butter</li>
            <li>A dash of love and patience!</li>
          </ul>

          <h3 style={{ fontSize: '1.5rem', color: '#333', marginBottom: '15px' }}>Step-by-Step Instructions</h3>
          <ol style={{ fontSize: '1.1rem', color: '#444', lineHeight: '1.8', paddingLeft: '20px' }}>
            <li style={{ marginBottom: '10px' }}><strong>Prep Work:</strong> Wash and chop all your fresh ingredients. Setup your cooking station.</li>
            <li style={{ marginBottom: '10px' }}><strong>The Base:</strong> Heat your pan, add oil, and gently sauté your aromatics until fragrant.</li>
            <li style={{ marginBottom: '10px' }}><strong>The Core:</strong> Introduce the main components of {dishName}. Let the flavors meld together.</li>
            <li style={{ marginBottom: '10px' }}><strong>Simmer & Season:</strong> Add your liquids and spices. Cover and simmer to perfection.</li>
            <li style={{ marginBottom: '10px' }}><strong>Garnish & Serve:</strong> Plate beautifully, garnish with fresh herbs, and enjoy your amazing creation!</li>
          </ol>

        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
