import { motion } from 'framer-motion';
import { chefStories } from '../data/chefStories';
import { ChevronRight } from 'lucide-react';
import CookGuide3D from './CookGuide3D';
import ImageWithLoader from './ImageWithLoader';

export default function ChefStoriesAndMap({ onViewAllStories, onCookChat }) {
  return (
    <div style={{ padding: '60px 5%', display: 'flex', gap: '30px', height: '80vh', minHeight: '600px' }}>
      
      {/* Left Card: Chef Stories (Podcasts) */}
      <motion.div 
        initial={{ x: -50, opacity: 0 }}
        whileInView={{ x: 0, opacity: 1 }}
        viewport={{ once: true }}
        style={{ flex: 1, background: '#2C2C2C', borderRadius: '30px', padding: '30px', display: 'flex', flexDirection: 'column', boxShadow: '0 30px 60px rgba(0,0,0,0.3)', border: '1px solid #444', overflow: 'hidden' }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <h2 style={{ fontSize: '2.5rem', color: '#FFF', margin: 0 }}>Chef Stories</h2>
          <button onClick={onViewAllStories} style={{ background: 'transparent', color: '#FF7A30', border: 'none', fontSize: '1rem', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
            View All 25 <ChevronRight size={20} />
          </button>
        </div>

        {/* Scrollable list of stories */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px', paddingRight: '10px' }}>
          {chefStories.slice(0, 5).map(story => (
            <div key={story.id} style={{ display: 'flex', gap: '20px', background: '#1A1A1A', borderRadius: '20px', padding: '15px', alignItems: 'center', border: '1px solid #333' }}>
              <div style={{ width: '100px', height: '100px', borderRadius: '15px', overflow: 'hidden', flexShrink: 0 }}>
                <ImageWithLoader src={story.dishPic} alt={story.dishName} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
              <div style={{ flex: 1 }}>
                <h4 style={{ margin: '0 0 5px 0', color: '#FFF', fontSize: '1.2rem' }}>{story.dishName}</h4>
                <div style={{ color: '#FF7A30', fontWeight: 'bold', marginBottom: '10px' }}>{story.chefName} • {story.country}</div>
                <p style={{ margin: 0, color: '#AAA', fontSize: '0.9rem', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  "{story.quote}"
                </p>
                <div style={{ marginTop: '12px' }}>
                  {(story.podcastAudioUrl.includes('embed') || story.podcastAudioUrl.includes('acast')) ? (
                    <iframe 
                      title={story.dishName}
                      src={story.podcastAudioUrl} 
                      style={{ width: '100%', height: '120px', borderRadius: '10px', border: 'none', background: '#2C2C2C' }}
                      sandbox="allow-forms allow-popups allow-same-origin allow-scripts allow-top-navigation-by-user-activation"
                      allow="autoplay *; encrypted-media *;"
                    />
                  ) : (
                    <a 
                      href={story.podcastAudioUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        background: 'rgba(255,255,255,0.08)',
                        color: '#FF7A30',
                        padding: '8px 16px',
                        borderRadius: '20px',
                        textDecoration: 'none',
                        fontSize: '0.85rem',
                        fontWeight: 'bold',
                        border: '1px solid rgba(255,122,48,0.3)',
                        transition: 'all 0.2s'
                      }}
                      onMouseOver={e => { e.currentTarget.style.background = 'rgba(255,122,48,0.15)'; }}
                      onMouseOut={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; }}
                    >
                      🎧 Listen to Podcast on Web
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
          <button onClick={onViewAllStories} style={{ background: '#FF7A30', color: '#FFF', border: 'none', padding: '15px', borderRadius: '20px', fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer', marginTop: '10px' }}>
            Read & Listen to the Masterpieces
          </button>
        </div>
      </motion.div>

      {/* Right Card: 3D Master Chef Guide (Replacing the old map) */}
      <motion.div 
        initial={{ x: 50, opacity: 0 }}
        whileInView={{ x: 0, opacity: 1 }}
        viewport={{ once: true }}
        style={{ flex: 1, borderRadius: '30px', display: 'flex', flexDirection: 'column', boxShadow: '0 30px 60px rgba(0,0,0,0.3)', border: '1px solid #444', overflow: 'hidden' }}
      >
        <CookGuide3D onCookChat={onCookChat} />
      </motion.div>

    </div>
  );
}
