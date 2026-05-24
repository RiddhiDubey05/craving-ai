import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Mic, MicOff, MessageSquare } from 'lucide-react';

export default function MapFrog({ timeOfDay, isExploring }) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [frogMessage, setFrogMessage] = useState("Let's explore the culinary world!");
  
  useEffect(() => {
    const handleFrogSpeak = (e) => speak(e.detail);
    window.addEventListener('frog-speak', handleFrogSpeak);
    return () => window.removeEventListener('frog-speak', handleFrogSpeak);
  }, []);

  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const text = event.results[0][0].transcript;
        setTranscript(text);
        respondToUser(text);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, [timeOfDay]);

  const speak = (text) => {
    setFrogMessage(text);
    if (synthRef.current) {
      synthRef.current.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.pitch = 1.2; // Slightly higher pitch for the frog
      utterance.rate = 0.9;
      synthRef.current.speak(utterance);
    }
  };

  const respondToUser = (text) => {
    const lowerText = text.toLowerCase();
    let response = "I heard you! Let's find some food.";
    
    if (lowerText.includes('hungry') || lowerText.includes('food')) {
      response = "I can smell something delicious nearby! Let's check the map.";
    } else if (lowerText.includes('ramen')) {
      response = "You're near a hidden ramen place locals love 🌙🍜";
    } else if (lowerText.includes('coffee') || lowerText.includes('cafe')) {
      response = "That cafe smells amazing right now ☕✨";
    } else if (lowerText.includes('dessert') || lowerText.includes('sweet')) {
      response = "Late-night dessert run? I strongly support this decision 🍰";
    }

    speak(response);
  };

  const toggleListen = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current?.start();
        setIsListening(true);
      } catch (e) {
        console.error("Speech recognition error:", e);
      }
    }
  };

  // Frog Animation States
  const frogVariants = {
    idle: { y: [0, -5, 0], transition: { duration: 3, repeat: Infinity, ease: "easeInOut" } },
    listening: { scale: [1, 1.05, 1], y: [0, -10, 0], transition: { duration: 1, repeat: Infinity } },
    sleepy: { y: [0, 2, 0], opacity: 0.8, transition: { duration: 4, repeat: Infinity } }
  };

  const currentAnimation = isListening ? 'listening' : (timeOfDay === 'night' && !isExploring ? 'sleepy' : 'idle');

  return (
    <div style={{ position: 'fixed', bottom: '30px', right: '30px', zIndex: 9999, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '15px' }}>
      
      {/* Dialogue Bubble */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        key={frogMessage}
        style={{
          background: 'rgba(255, 255, 255, 0.95)',
          padding: '15px 25px',
          borderRadius: '25px 25px 5px 25px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.2)',
          maxWidth: '250px',
          color: '#333',
          fontWeight: 'bold',
          fontSize: '1rem',
          position: 'relative'
        }}
      >
        {frogMessage}
        {isListening && <div style={{ fontSize: '0.8rem', color: '#FF7A30', marginTop: '5px' }}>Listening...</div>}
      </motion.div>

      {/* The Frog Body */}
      <div style={{ position: 'relative', width: '120px', height: '120px' }}>
        <motion.div
          variants={frogVariants}
          animate={currentAnimation}
          style={{
            width: '100px', height: '90px',
            background: '#4DB6AC', // Soft teal body
            borderRadius: '50% 50% 40% 40%',
            position: 'absolute',
            bottom: 0, right: 0,
            boxShadow: 'inset -10px -10px 20px rgba(0,0,0,0.1), 0 10px 20px rgba(0,0,0,0.3)',
            display: 'flex', flexDirection: 'column', alignItems: 'center'
          }}
        >
          {/* Eyes */}
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '60%', marginTop: '15px' }}>
            <div style={{ width: '20px', height: '25px', background: '#FFF', borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <motion.div 
                animate={{ scaleY: timeOfDay === 'night' && !isListening ? [1, 0.1, 1] : [1, 0.1, 1] }} 
                transition={{ duration: 4, repeat: Infinity, times: [0, 0.1, 0.2] }}
                style={{ width: '10px', height: '12px', background: '#333', borderRadius: '50%' }} 
              />
            </div>
            <div style={{ width: '20px', height: '25px', background: '#FFF', borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
              <motion.div 
                animate={{ scaleY: timeOfDay === 'night' && !isListening ? [1, 0.1, 1] : [1, 0.1, 1] }} 
                transition={{ duration: 4, repeat: Infinity, times: [0, 0.1, 0.2] }}
                style={{ width: '10px', height: '12px', background: '#333', borderRadius: '50%' }} 
              />
            </div>
          </div>

          {/* Blush & Smile */}
          <div style={{ display: 'flex', justifyContent: 'space-between', width: '70%', marginTop: '5px' }}>
            <div style={{ width: '15px', height: '8px', background: '#FF8A65', borderRadius: '50%', opacity: 0.6 }} />
            <div style={{ width: '15px', height: '8px', background: '#FF8A65', borderRadius: '50%', opacity: 0.6 }} />
          </div>
          
          <div style={{ 
            width: '12px', height: '6px', 
            borderBottom: '3px solid #333', 
            borderRadius: '0 0 10px 10px', 
            marginTop: '-5px' 
          }} />

          {/* Scarf */}
          <div style={{ 
            width: '85px', height: '20px', 
            background: '#FF7A30', 
            borderRadius: '10px', 
            position: 'absolute', bottom: '10px',
            boxShadow: '0 5px 10px rgba(0,0,0,0.2)'
          }} />

          {/* Cream Belly overlay */}
          <div style={{
            width: '60px', height: '30px',
            background: '#F5F5DC',
            borderRadius: '50% 50% 0 0',
            position: 'absolute', bottom: 0,
            opacity: 0.8
          }} />
        </motion.div>
      </div>

      {/* Text Chat and Voice Control */}
      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
        <input 
          type="text" 
          placeholder="Ask Froggy..." 
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.target.value.trim()) {
              respondToUser(e.target.value.trim());
              e.target.value = '';
            }
          }}
          style={{
            padding: '12px 20px',
            borderRadius: '25px',
            border: 'none',
            outline: 'none',
            boxShadow: '0 5px 15px rgba(0,0,0,0.2)',
            fontSize: '1rem',
            width: '200px'
          }}
        />

        <button 
          onClick={toggleListen}
          style={{
            background: isListening ? '#F44336' : '#FF7A30',
            color: '#FFF',
            border: 'none',
            padding: '15px',
            borderRadius: '50%',
            cursor: 'pointer',
            boxShadow: '0 5px 15px rgba(0,0,0,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.3s'
          }}
        >
          {isListening ? <MicOff size={24} /> : <Mic size={24} />}
        </button>
      </div>

    </div>
  );
}
