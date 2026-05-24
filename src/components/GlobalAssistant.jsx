import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, MessageSquare } from 'lucide-react';

// Using the provided Capybara images for different states
const CAPY_EATING = "https://i.pinimg.com/736x/8a/24/bb/8a24bb89656a1b24b89656a1b24b8965.jpg"; // Mocked url based on image 3
const CAPY_DRINKING = "https://i.pinimg.com/736x/8a/24/bb/8a24bb89656a1b24b89656a1b24b8966.jpg"; 

export default function GlobalAssistant() {
  const [isTalking, setIsTalking] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState("Hey! I'm your Capybara chef. Want to order or cook?");
  
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      
      recognitionRef.current.onstart = () => setIsListening(true);
      
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setChatMessage(`You asked: "${transcript}". Let me pull up a recipe for you!`);
        setIsChatOpen(true);
        setTimeout(() => speakResponse("I can guide you step by step. First, let's gather the ingredients."), 1000);
      };
      
      recognitionRef.current.onend = () => setIsListening(false);
      recognitionRef.current.onerror = () => setIsListening(false);
    }
  }, []);

  const speakResponse = (text) => {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    
    setChatMessage(text);
    setIsTalking(true);
    setIsChatOpen(true);
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.pitch = 0.9; // Deeper, chill capybara voice
    utterance.rate = 0.9;
    
    utterance.onend = () => setIsTalking(false);
    synthRef.current.speak(utterance);
  };

  const handleToggleListen = (e) => {
    e.stopPropagation();
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
    } else if (recognitionRef.current) {
      if (!isTalking) setChatMessage("Listening to your cravings...");
      setIsChatOpen(true);
      recognitionRef.current.start();
    }
  };

  // Allow triggering recipes from other components globally
  useEffect(() => {
    const handleTriggerRecipe = (e) => {
      const { dish } = e.detail;
      speakResponse(`You want to make ${dish}? Great choice! I'll guide you step by step.`);
    };
    window.addEventListener('trigger-recipe', handleTriggerRecipe);
    return () => window.removeEventListener('trigger-recipe', handleTriggerRecipe);
  }, []);

  return (
    <div style={{ position: 'fixed', bottom: '30px', right: '30px', zIndex: 9999, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '15px' }}>
      
      {/* Chat Interface */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            style={{
              background: 'rgba(255,255,255,0.95)',
              backdropFilter: 'blur(20px)',
              padding: '20px',
              borderRadius: '20px 20px 0 20px',
              position: 'fixed', bottom: '100px', right: '30px',
              width: '350px', height: '500px', background: '#FFF',
              borderRadius: '24px', boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
              zIndex: 9999, border: '2px solid #FFC857'
            }}
          >
            {/* Header */}
            <div style={{ background: '#FFC857', padding: '15px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '50%', overflow: 'hidden', border: '2px solid #FFF' }}>
                  <img src="https://media.tenor.com/7gK5Yh6pEQcAAAAi/capybara-eating.gif" alt="Chef Capy" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={(e) => { e.target.src = "https://images.unsplash.com/photo-1698778573682-346d219402b5?w=400&q=80"; }} />
                </div>
                <h3 style={{ margin: 0, color: '#333' }}>Chef Capy</h3>
              </div>
              <button onClick={() => setIsOpen(false)} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#333' }}>
                <X size={24} />
              </button>
            </div>

            {/* Chat History */}
            <div style={{ flex: 1, padding: '20px', overflowY: 'auto', background: '#FAFAFA', display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%' }}>
                  <div style={{ 
                    background: msg.role === 'user' ? '#FF7A30' : '#FFF',
                    color: msg.role === 'user' ? '#FFF' : '#333',
                    padding: '12px 16px', borderRadius: '15px',
                    borderBottomRightRadius: msg.role === 'user' ? '4px' : '15px',
                    borderBottomLeftRadius: msg.role === 'ai' ? '4px' : '15px',
                    boxShadow: '0 4px 10px rgba(0,0,0,0.05)',
                    border: msg.role === 'ai' ? '1px solid #EEE' : 'none'
                  }}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {isTyping && (
                <div style={{ alignSelf: 'flex-start', background: '#FFF', padding: '12px 16px', borderRadius: '15px', borderBottomLeftRadius: '4px', border: '1px solid #EEE', display: 'flex', gap: '5px' }}>
                  <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0 }} style={{ width: '8px', height: '8px', background: '#CCC', borderRadius: '50%' }} />
                  <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }} style={{ width: '8px', height: '8px', background: '#CCC', borderRadius: '50%' }} />
                  <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }} style={{ width: '8px', height: '8px', background: '#CCC', borderRadius: '50%' }} />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSend} style={{ padding: '15px', background: '#FFF', borderTop: '1px solid #EEE', display: 'flex', gap: '10px', alignItems: 'center' }}>
              <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Chef Capy..."
                style={{ flex: 1, border: '1px solid #DDD', padding: '12px', borderRadius: '20px', outline: 'none' }}
              />
              <button type="submit" style={{ background: '#FFC857', border: 'none', width: '40px', height: '40px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#333' }}>
                <Send size={18} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Floating Trigger Button */}
      <motion.div
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100px',
          height: '100px',
          borderRadius: '50%',
          boxShadow: '0 15px 30px rgba(0,0,0,0.3)',
          cursor: 'pointer',
          position: 'relative',
          background: '#FFF',
          overflow: 'hidden',
          border: '4px solid #FFC857'
        }}
      >
        <img 
          src="https://images.unsplash.com/photo-1698778573682-346d219402b5?w=400&q=80" 
          alt="Chef Capy"
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
        
        {/* Mic Toggle Button */}
        <div 
          onClick={handleToggleListen}
          style={{ position: 'absolute', bottom: '0', right: '0', background: isListening ? '#E23744' : '#FF7A30', borderRadius: '50%', padding: '8px', boxShadow: '0 4px 10px rgba(0,0,0,0.3)', cursor: 'pointer', zIndex: 10 }}
        >
          {isListening ? <MicOff size={16} color="#FFF" /> : <Mic size={16} color="#FFF" />}
        </div>
      </motion.div>
    </div>
  );
}
