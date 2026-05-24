import { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Mic, Search } from 'lucide-react';

export default function HeroSearch({ onSearch, isSearching }) {
  const [query, setQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if(query.trim()) onSearch(query);
  };

  const toggleVoice = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice not supported in this browser.");
      return;
    }

    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.continuous = false;
    
    recognition.onstart = () => setIsRecording(true);
    recognition.onresult = (e) => {
      const text = e.results[0][0].transcript;
      setQuery(text);
      onSearch(text); // Auto submit voice
    };
    recognition.onend = () => setIsRecording(false);
    
    recognition.start();
  };

  return (
    <div style={{ position: 'relative', width: '80%', maxWidth: '800px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      
      {/* The Frog Companion */}
      <motion.div 
        animate={{ y: [0, -10, 0] }}
        transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
        style={{ marginBottom: '20px', width: '150px' }}
      >
        <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Base Body */}
          <circle cx="50" cy="60" r="35" fill="#88D49E"/>
          {/* Eyes */}
          <circle cx="35" cy="40" r="15" fill="#88D49E"/>
          <circle cx="65" cy="40" r="15" fill="#88D49E"/>
          <circle cx="35" cy="40" r="12" fill="white"/>
          <circle cx="65" cy="40" r="12" fill="white"/>
          {/* Pupils (Animate based on listening state) */}
          <motion.circle cx="35" cy="40" r={isRecording ? 8 : 6} fill="#2C2C2C" animate={{ r: isRecording ? 8 : 6 }}/>
          <motion.circle cx="65" cy="40" r={isRecording ? 8 : 6} fill="#2C2C2C" animate={{ r: isRecording ? 8 : 6 }}/>
          {/* Blushes */}
          <circle cx="28" cy="55" r="5" fill={isRecording ? "#FF7A30" : "#FF5A4E"} opacity="0.6"/>
          <circle cx="72" cy="55" r="5" fill={isRecording ? "#FF7A30" : "#FF5A4E"} opacity="0.6"/>
          {/* Mouth */}
          {isRecording ? (
             <ellipse cx="50" cy="58" rx="8" ry="12" fill="#2C2C2C" />
          ) : (
             <path d="M 40 55 Q 50 65 60 55" stroke="#2C2C2C" strokeWidth="3" strokeLinecap="round" fill="none"/>
          )}
        </svg>
      </motion.div>

      {/* Input Bar */}
      <form 
        onSubmit={handleSubmit}
        className="glass-panel interactive"
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          padding: '10px 20px',
          boxShadow: '0 20px 40px rgba(255,122,48,0.15)',
          background: 'rgba(255,255,255,0.7)'
        }}
      >
        <Search size={28} color="var(--accent-primary)" />
        <input 
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder={isRecording ? "Listening to your cravings..." : "Spicy biryani under ₹300 nearby..."}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            fontSize: '1.5rem',
            padding: '15px 20px',
            color: 'var(--text-dark)',
            fontWeight: '600'
          }}
        />
        <motion.button 
          type="button"
          onClick={toggleVoice}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          style={{
            background: isRecording ? 'var(--accent-primary)' : 'transparent',
            border: 'none',
            borderRadius: '50%',
            padding: '12px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: isRecording ? '0 0 20px var(--accent-primary)' : 'none'
          }}
        >
          <Mic size={28} color={isRecording ? 'white' : 'var(--text-dark)'} />
        </motion.button>
      </form>
      
      {isSearching && (
        <motion.div 
          initial={{ opacity: 0 }} 
          animate={{ opacity: 1 }} 
          style={{ marginTop: '20px', color: 'var(--accent-primary)', fontWeight: 'bold' }}
        >
          Cooking up your results...
        </motion.div>
      )}
    </div>
  );
}
