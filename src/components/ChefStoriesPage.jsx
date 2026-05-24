import { useState } from 'react';
import { motion } from 'framer-motion';
import { chefStories } from '../data/chefStories';
import { PlayCircle, PauseCircle, Headphones } from 'lucide-react';

export default function ChefStoriesPage({ onBack }) {
  const [playingAudio, setPlayingAudio] = useState(null);
  const [playingId, setPlayingId] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const toggleAudio = (id, storyText) => {
    if (playingId === id) {
      window.speechSynthesis.cancel();
      setPlayingId(null);
      setCurrentTime(0);
      clearInterval(window.podcastInterval);
    } else {
      window.speechSynthesis.cancel();
      clearInterval(window.podcastInterval);
      
      const estimatedDuration = Math.ceil((storyText.split(' ').length / 150) * 60); // 150 words per min
      setDuration(estimatedDuration);
      setCurrentTime(0);
      
      const utterance = new SpeechSynthesisUtterance(storyText);
      
      // Attempt to load an English voice to prevent silent failures
      const voices = window.speechSynthesis.getVoices();
      const enVoice = voices.find(v => v.lang.startsWith('en'));
      if (enVoice) utterance.voice = enVoice;
      
      utterance.pitch = 1.0;
      utterance.rate = 0.9; // Nice and slow like a podcast
      
      utterance.onend = () => {
        setPlayingId(null);
        setCurrentTime(0);
        clearInterval(window.podcastInterval);
      };

      // Slight delay to ensure cancel() finishes
      setTimeout(() => {
        window.speechSynthesis.speak(utterance);
        setPlayingId(id);
      }, 50);

      window.podcastInterval = setInterval(() => {
        setCurrentTime(prev => {
          if (prev >= estimatedDuration) return prev;
          return prev + 1;
        });
      }, 1000);
    }
  };

  const handleSeek = (e) => {
    // Cannot natively seek SpeechSynthesis, visual only
  };

  const formatTime = (time) => {
    if (isNaN(time)) return "00:00";
    const m = Math.floor(time / 60).toString().padStart(2, '0');
    const s = Math.floor(time % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div style={{ width: '100vw', minHeight: '100vh', background: '#1A1A1A', overflowX: 'hidden', color: '#FFF' }}>
      
      {/* Header */}
      <div style={{ padding: '60px 5%', background: 'linear-gradient(to right, #000000, #434343)', borderBottom: '2px solid #FF7A30' }}>
        <button onClick={onBack} style={{ background: 'transparent', color: '#FF7A30', border: '1px solid #FF7A30', padding: '10px 20px', borderRadius: '20px', cursor: 'pointer', marginBottom: '30px', fontWeight: 'bold' }}>
          ← Back to the World
        </button>
        <h1 style={{ fontSize: '4rem', fontWeight: '900', margin: 0, color: '#FFF' }}>The 25 Masterpieces</h1>
        <p style={{ fontSize: '1.2rem', color: '#AAA', marginTop: '10px', maxWidth: '600px' }}>
          Read their deep, untold origins and listen to the exclusive podcast interviews while you explore the history served on a plate.
        </p>
      </div>

      {/* Deep Story Grid */}
      <div style={{ padding: '60px 5%', display: 'flex', flexDirection: 'column', gap: '80px' }}>
        {chefStories.map((story) => (
          <motion.div
            key={story.id}
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.8 }}
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              background: '#2C2C2C',
              borderRadius: '30px',
              overflow: 'hidden',
              boxShadow: '0 30px 60px rgba(0,0,0,0.5)',
              border: '1px solid #444'
            }}
          >
            {/* Left: Images */}
            <div style={{ flex: '1 1 400px', position: 'relative', minHeight: '400px' }}>
              <img src={story.dishPic} alt={story.dishName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              
              {/* Overlay Chef Photo */}
              <div style={{ position: 'absolute', bottom: '20px', right: '20px', width: '120px', height: '120px', borderRadius: '50%', overflow: 'hidden', border: '4px solid #FF7A30', boxShadow: '0 10px 20px rgba(0,0,0,0.5)' }}>
                <img src={story.chefPic} alt={story.chefName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
              
              <div style={{ position: 'absolute', top: '20px', left: '20px', background: 'rgba(0,0,0,0.8)', padding: '5px 15px', borderRadius: '20px', fontWeight: 'bold', color: '#FF7A30' }}>
                {story.country}
              </div>
            </div>
            
            {/* Right: Deep Content & Podcast */}
            <div style={{ flex: '1 1 500px', padding: '40px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <h3 style={{ margin: '0 0 10px 0', fontSize: '2.5rem', color: '#FFF' }}>{story.dishName}</h3>
              <h4 style={{ margin: '0 0 30px 0', color: '#FF7A30', fontSize: '1.2rem' }}>by {story.chefName}</h4>
              
              <blockquote style={{ margin: '0 0 30px 0', paddingLeft: '20px', borderLeft: '4px solid #FF7A30', fontStyle: 'italic', color: '#CCC', fontSize: '1.1rem' }}>
                "{story.quote}"
              </blockquote>
              
              <p style={{ lineHeight: 1.8, color: '#AAA', fontSize: '1.1rem', marginBottom: '40px' }}>
                {story.deepExplanation}
              </p>
              
              {/* Premium Podcast & AI Narration Panel */}
              <div style={{ background: '#1A1A1A', padding: '25px', borderRadius: '24px', border: '1px solid #444', marginTop: '25px' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'space-between', alignItems: 'center' }}>
                  
                  {/* AI Narrator Controls */}
                  <button 
                    onClick={() => toggleAudio(story.id, story.deepExplanation)}
                    style={{
                      background: playingId === story.id ? '#D32F2F' : '#FF7A30',
                      color: '#FFF',
                      border: 'none',
                      padding: '12px 24px',
                      borderRadius: '30px',
                      fontWeight: 'bold',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      transition: 'all 0.3s',
                      boxShadow: '0 5px 15px rgba(255,122,48,0.2)'
                    }}
                  >
                    {playingId === story.id ? <PauseCircle size={20} /> : <PlayCircle size={20} />}
                    {playingId === story.id ? 'Pause Narration' : 'Narrate Story (AI)'}
                  </button>

                  {/* External Podcast Link */}
                  {!(story.podcastAudioUrl.includes('embed') || story.podcastAudioUrl.includes('acast')) && (
                    <a 
                      href={story.podcastAudioUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{
                        background: 'rgba(255,255,255,0.1)',
                        color: '#FFF',
                        padding: '12px 24px',
                        borderRadius: '30px',
                        textDecoration: 'none',
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        border: '1px solid rgba(255,255,255,0.2)',
                        transition: 'background 0.3s'
                      }}
                      onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
                      onMouseOut={e => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                    >
                      <Headphones size={18} />
                      Listen on Web
                    </a>
                  )}
                </div>

                {/* Progress Bar (Only active narration) */}
                {playingId === story.id && (
                  <div style={{ marginTop: '20px', background: '#2C2C2C', padding: '15px', borderRadius: '15px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#AAA', fontSize: '0.85rem', marginBottom: '8px' }}>
                      <span>AI Voice Narrator</span>
                      <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
                    </div>
                    <div style={{ height: '6px', background: '#333', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', background: '#FF7A30', width: `${(currentTime / duration) * 100}%`, transition: 'width 1s linear' }} />
                    </div>
                  </div>
                )}

                {/* Embed Podcast Player if supported */}
                {(story.podcastAudioUrl.includes('embed') || story.podcastAudioUrl.includes('acast')) && (
                  <div style={{ marginTop: '20px' }}>
                    <iframe 
                      title={story.dishName}
                      src={story.podcastAudioUrl} 
                      style={{ width: '100%', height: '150px', borderRadius: '15px', border: 'none', background: '#2C2C2C' }}
                      sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-top-navigation-by-user-activation"
                      allow="autoplay *; encrypted-media *;"
                    />
                  </div>
                )}
              </div>
              
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
