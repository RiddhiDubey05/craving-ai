import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Send, ChefHat, Heart, Share2, Download, Printer, CheckCircle2, Circle, X, Mic } from 'lucide-react';
import CookGuide3D from './CookGuide3D';
import ImageWithLoader from './ImageWithLoader';
import { getImageUrl } from '../services/apiService';

function FocusMode({ recipe, onClose }) {
  const [currentStep, setCurrentStep] = useState(0);

  const totalSteps = recipe.steps.length;
  const progress = ((currentStep) / totalSteps) * 100;
  const isDone = currentStep >= totalSteps;

  const handleNext = () => {
    if (!isDone) {
      setCurrentStep(prev => prev + 1);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: '100%' }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      style={{
        position: 'fixed',
        top: 0, left: 0, right: 0, bottom: 0,
        background: '#FF7A30',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        color: '#FFF',
        overflow: 'hidden'
      }}
    >
      <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.2)' }}>
        <motion.div 
          animate={{ width: `${progress}%` }} 
          style={{ height: '100%', background: '#FFF' }}
        />
      </div>

      <div style={{ padding: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', opacity: 0.9 }}>Cooking Focus Mode</h2>
          <h1 style={{ margin: 0, fontSize: '2.5rem', fontWeight: '900' }}>{recipe.dishName}</h1>
        </div>
        <button 
          onClick={(e) => { e.stopPropagation(); onClose(); }}
          style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: '#FFF', width: '60px', height: '60px', borderRadius: '50%', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(10px)' }}
        >
          <X size={32} />
        </button>
      </div>

      <div 
        onClick={handleNext}
        style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '50px', cursor: 'pointer', position: 'relative' }}
      >
        <AnimatePresence mode="wait">
          {!isDone ? (
            <motion.div 
              key={currentStep}
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              style={{ textAlign: 'center', maxWidth: '1000px' }}
            >
              <div style={{ fontSize: '1.5rem', opacity: 0.8, marginBottom: '20px', textTransform: 'uppercase', letterSpacing: '2px', fontWeight: 'bold' }}>
                Step {currentStep + 1} of {totalSteps}
              </div>
              <h1 style={{ fontSize: '4.5rem', lineHeight: '1.3', fontWeight: '900', margin: 0, textShadow: '0 10px 30px rgba(0,0,0,0.1)' }}>
                {recipe.steps[currentStep]}
              </h1>
              <div style={{ marginTop: '50px', opacity: 0.6, fontSize: '1.2rem' }}>
                (Tap anywhere to go to next step)
              </div>
            </motion.div>
          ) : (
            <motion.div 
              key="done"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              style={{ textAlign: 'center' }}
            >
              <div style={{ width: '150px', height: '150px', borderRadius: '50%', background: '#FFF', color: '#FF7A30', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 30px', boxShadow: '0 20px 40px rgba(0,0,0,0.2)' }}>
                <CheckCircle2 size={80} />
              </div>
              <h1 style={{ fontSize: '5rem', fontWeight: '900', margin: 0 }}>Bon Appétit!</h1>
              <p style={{ fontSize: '2rem', opacity: 0.9 }}>You have finished cooking {recipe.dishName}.</p>
              <button 
                onClick={(e) => { e.stopPropagation(); onClose(); }}
                style={{ marginTop: '40px', background: '#FFF', color: '#FF7A30', border: 'none', padding: '20px 50px', fontSize: '1.5rem', borderRadius: '40px', cursor: 'pointer', fontWeight: 'bold', boxShadow: '0 10px 30px rgba(0,0,0,0.2)' }}
              >
                Return to Chat
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

function RecipeCard({ recipe, onStartFocus }) {
  const [checkedIngs, setCheckedIngs] = useState({});

  if (!recipe) return null;
  
  const imageUrl = getImageUrl(recipe.imageQuery || recipe.dishName);

  const toggleIngredient = (idx) => {
    setCheckedIngs(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      style={{
        background: '#FFF',
        borderRadius: '20px',
        overflow: 'hidden',
        boxShadow: '0 15px 35px rgba(0,0,0,0.1)',
        marginTop: '15px',
        width: '100%',
        maxWidth: '500px',
        border: '1px solid #EEE'
      }}
    >
      <div style={{ position: 'relative', height: '250px', width: '100%' }}>
        <ImageWithLoader src={imageUrl} alt={recipe.dishName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'linear-gradient(to bottom, transparent 50%, rgba(0,0,0,0.8))' }} />
        <h3 style={{ position: 'absolute', bottom: '20px', left: '20px', color: '#FFF', margin: 0, fontSize: '1.5rem', fontWeight: 'bold', textShadow: '0 2px 4px rgba(0,0,0,0.5)' }}>
          {recipe.dishName}
        </h3>
        <div style={{ position: 'absolute', top: '15px', right: '15px', display: 'flex', gap: '10px' }}>
          <button style={{ width: '35px', height: '35px', borderRadius: '50%', background: '#FFF', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }}><Heart size={18} color="#FF4757" /></button>
          <button style={{ width: '35px', height: '35px', borderRadius: '50%', background: '#FFF', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }}><Share2 size={18} color="#333" /></button>
        </div>
      </div>
      
      <div style={{ padding: '25px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <span style={{ background: '#FFF0E6', color: '#FF7A30', padding: '5px 15px', borderRadius: '20px', fontSize: '0.85rem', fontWeight: 'bold' }}>AI Generated</span>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button style={{ background: '#F8F9FA', border: 'none', padding: '8px 12px', borderRadius: '10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.85rem' }}><Printer size={16} /> Print</button>
            <button style={{ background: '#F8F9FA', border: 'none', padding: '8px 12px', borderRadius: '10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.85rem' }}><Download size={16} /> Save</button>
          </div>
        </div>

        <button 
          onClick={() => onStartFocus(recipe)}
          style={{ width: '100%', background: '#FF7A30', color: '#FFF', border: 'none', padding: '15px', borderRadius: '15px', fontSize: '1.1rem', fontWeight: 'bold', cursor: 'pointer', marginBottom: '25px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', boxShadow: '0 10px 20px rgba(255,122,48,0.3)' }}
        >
          <ChefHat size={20} /> Start Cooking Mode
        </button>

        <h4 style={{ color: '#333', borderBottom: '2px solid #FF7A30', paddingBottom: '10px', display: 'inline-block', marginBottom: '15px' }}>Ingredients Tracker</h4>
        <ul style={{ padding: 0, margin: '0 0 25px 0', listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {recipe.ingredients?.map((ing, idx) => {
            const isChecked = checkedIngs[idx];
            return (
              <li 
                key={idx} 
                onClick={() => toggleIngredient(idx)}
                style={{ 
                  display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 15px', background: isChecked ? '#F8F9FA' : '#FFF', border: '1px solid #EEE', borderRadius: '12px', cursor: 'pointer', transition: 'all 0.2s',
                  opacity: isChecked ? 0.6 : 1
                }}
              >
                {isChecked ? <CheckCircle2 color="#2ED573" size={20} /> : <Circle color="#DDD" size={20} />}
                <span style={{ fontSize: '1.05rem', color: isChecked ? '#888' : '#333', textDecoration: isChecked ? 'line-through' : 'none' }}>
                  {ing}
                </span>
              </li>
            );
          })}
        </ul>

        <h4 style={{ color: '#333', borderBottom: '2px solid #FF7A30', paddingBottom: '10px', display: 'inline-block', marginBottom: '15px' }}>Instructions Preview</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {recipe.steps?.map((step, idx) => (
            <div key={idx} style={{ display: 'flex', gap: '15px' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#FFF0E6', color: '#FF7A30', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', flexShrink: 0 }}>
                {idx + 1}
              </div>
              <p style={{ margin: 0, color: '#666', lineHeight: '1.6', fontSize: '0.95rem' }}>{step}</p>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

export default function CookChatPage({ onBack, initialMessage, userName = 'Friend' }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [activeFocusRecipe, setActiveFocusRecipe] = useState(null);
  
  const languages = [
    { name: 'English', code: 'en-US' },
    { name: 'Hindi', code: 'hi-IN' },
    { name: 'Telugu', code: 'te-IN' },
    { name: 'French', code: 'fr-FR' },
    { name: 'German', code: 'de-DE' }
  ];
  const [selectedLanguage, setSelectedLanguage] = useState(languages[0]);
  
  const messagesEndRef = useRef(null);
  const hasGreeted = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const initChat = async () => {
      if (hasGreeted.current) return;
      hasGreeted.current = true;
      
      let city = 'your city';
      try {
        const res = await fetch('https://ipapi.co/json/');
        const data = await res.json();
        if (data.city) city = data.city;
      } catch (e) {
        console.warn("Location fetch failed");
      }
      
      const greeting = `Bonjour! I am your 3D Master Chef! I see you are cooking from ${city}! Let's make something amazing. What ingredients do you have in your kitchen right now?`;
      
      setMessages([{ sender: 'chef', text: greeting, city }]);
      speakText(greeting, 'en-US');

      if (initialMessage) {
        setTimeout(() => {
          handleSend(initialMessage);
        }, 3000); // Wait a bit for the greeting to start before firing the user's intent
      }
    };
    
    initChat();
  }, [initialMessage]);

  const speakText = (text, langCode = selectedLanguage.code) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); 
      
      // Split text into sentences to avoid Chrome's long-text cutoff bug
      const chunks = text.match(/[^.!?]+[.!?]+/g) || [text];

      chunks.forEach((chunk, index) => {
        const trimmedChunk = chunk.trim();
        if (!trimmedChunk) return;

        const utterance = new SpeechSynthesisUtterance(trimmedChunk);
        utterance.lang = langCode; // Ensures consistent pronunciation without randomly swapping to a specific voice once loaded

        if (index === 0) {
          utterance.onstart = () => setIsSpeaking(true);
        }
        if (index === chunks.length - 1) {
          utterance.onend = () => setIsSpeaking(false);
        }

        window.speechSynthesis.speak(utterance);
      });
    }
  };

  const handleSend = async (forcedText = null) => {
    if (isTyping) return; // Prevent double sending if user spams enter

    const textToSend = forcedText || input;
    if (!textToSend.trim()) return;

    const userMessage = { sender: 'user', text: textToSend.trim() };
    
    setInput('');
    setIsTyping(true);

    // Update state purely
    setMessages(prev => [...prev, userMessage]);
    
    // Call backend outside of the state updater function to prevent StrictMode double-fire
    sendToBackend([...messages, userMessage]);
  };

  const sendToBackend = async (chatHistory) => {
    try {
      const apiHistory = chatHistory.filter(msg => !msg.isSystemLocation);
      const response = await fetch('http://localhost:3001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: apiHistory, language: selectedLanguage.name, userName: userName })
      });
      
      if (!response.ok) throw new Error("API Limit Reached");

      const data = await response.json();
      setIsTyping(false);
      
      const chefReply = { sender: 'chef', text: data.spoken_dialogue, recipe_card: data.recipe_card };
      setMessages(prev => [...prev, chefReply]);
      speakText(data.spoken_dialogue);
      
    } catch (error) {
      setIsTyping(false);
      const errorMsg = "Mon Dieu! My connection to the kitchen is broken. Please try again!";
      setMessages(prev => [...prev, { sender: 'chef', text: errorMsg }]);
    }
  };

  const isChefActive = isTyping || isSpeaking;

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#F8F9FA', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      
      <AnimatePresence>
        {activeFocusRecipe && (
          <FocusMode 
            recipe={activeFocusRecipe} 
            onClose={() => setActiveFocusRecipe(null)} 
          />
        )}
      </AnimatePresence>

      <div style={{ background: '#FF7A30', padding: '15px 30px', display: 'flex', alignItems: 'center', gap: '20px', color: '#FFF', boxShadow: '0 5px 15px rgba(0,0,0,0.1)', zIndex: 10 }}>
        <button 
          onClick={() => {
            window.speechSynthesis.cancel();
            onBack();
          }}
          style={{ background: 'transparent', border: 'none', color: '#FFF', cursor: 'pointer', padding: '10px' }}
        >
          <ArrowLeft size={24} />
        </button>
        <h1 style={{ margin: 0, fontSize: '1.3rem', fontWeight: '900', flex: 1 }}>cookAIfood Studio</h1>
        <select 
          value={selectedLanguage.name}
          onChange={(e) => {
            const newLang = languages.find(l => l.name === e.target.value);
            setSelectedLanguage(newLang);
            speakText(`I am now speaking ${newLang.name}!`, newLang.code);
          }}
          style={{ background: 'rgba(255,255,255,0.2)', color: '#FFF', border: '1px solid rgba(255,255,255,0.4)', padding: '8px 15px', borderRadius: '20px' }}
        >
          {languages.map(l => <option key={l.code} value={l.name} style={{ color: '#333' }}>{l.name}</option>)}
        </select>
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style={{ width: '40%', height: '100%', background: 'radial-gradient(circle at center, #FFF5ED 0%, #FFE5D4 100%)', borderRight: '1px solid rgba(0,0,0,0.05)', position: 'relative' }}>
          <CookGuide3D isChatMode={true} isTalking={isChefActive} />
        </div>

        <div style={{ width: '60%', height: '100%', display: 'flex', flexDirection: 'column', background: '#FAFAFA' }}>
          <div style={{ flex: 1, overflowY: 'auto', padding: '40px', display: 'flex', flexDirection: 'column', gap: '25px' }}>
            {messages.map((msg, i) => (
              <motion.div key={i} style={{ alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
                <div style={{ background: msg.sender === 'user' ? '#4A90E2' : '#FFF', color: msg.sender === 'user' ? '#FFF' : '#333', padding: '15px 25px', borderRadius: msg.sender === 'user' ? '25px 25px 5px 25px' : '25px 25px 25px 5px', boxShadow: '0 5px 15px rgba(0,0,0,0.05)' }}>
                  {msg.text}
                </div>
                {msg.recipe_card && <RecipeCard recipe={msg.recipe_card} onStartFocus={setActiveFocusRecipe} />}
              </motion.div>
            ))}
            {isTyping && <div style={{ color: '#888' }}>Chef is cooking...</div>}
            <div ref={messagesEndRef} />
          </div>

          <div style={{ padding: '25px 40px', background: '#FFF', borderTop: '1px solid #EAEAEA', display: 'flex', gap: '15px' }}>
            <input 
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Type your ingredients or questions..."
              style={{ flex: 1, padding: '18px 25px', borderRadius: '30px', border: '1px solid #DDD', fontSize: '1.1rem', outline: 'none' }}
            />
            <button 
              onClick={() => handleSend()}
              disabled={!input.trim() || isTyping}
              style={{ background: '#FF7A30', color: '#FFF', border: 'none', width: '60px', height: '60px', borderRadius: '50%', cursor: 'pointer' }}
            >
              <Send size={24} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
