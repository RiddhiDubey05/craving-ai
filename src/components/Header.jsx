import { useState } from 'react';
import { User, Settings, Lock, Trash2, Edit3, MapPin } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function Header({ currentCity, onOpenProfile }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 20 }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        padding: '20px 5%',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        zIndex: 1000,
        background: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        WebkitBackdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}
    >
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
        <div style={{ width: '40px', height: '40px', background: '#FFC857', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#B71C1C', fontWeight: '900', fontSize: '1.2rem' }}>
          C
        </div>
        <h2 style={{ margin: 0, fontSize: '1.6rem', fontWeight: '800', color: '#FFF', textShadow: '0 2px 4px rgba(0,0,0,0.3)' }}>CravingAI.</h2>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <button
          type="button"
          onClick={onOpenProfile}
          style={{
            border: '1px solid rgba(255,255,255,0.35)',
            background: 'rgba(255,255,255,0.16)',
            color: '#FFF',
            borderRadius: '999px',
            padding: '10px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer',
            fontWeight: 800,
            maxWidth: '42vw',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}
          title="Change location"
        >
          <MapPin size={16} />
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{currentCity || 'Set location'}</span>
        </button>

        <div style={{ position: 'relative' }}>
          <motion.div
            whileHover={{ scale: 1.05 }}
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            style={{
              width: '45px',
              height: '45px',
              borderRadius: '50%',
              background: 'rgba(255, 255, 255, 0.2)',
              border: '2px solid #FFC857',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 10px rgba(0,0,0,0.3)',
              flexShrink: 0,
              color: '#FFF'
            }}
          >
            <User size={24} />
          </motion.div>

          <AnimatePresence>
            {isMenuOpen && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95, pointerEvents: 'none' }}
                style={{
                  position: 'absolute',
                  top: '60px',
                  right: 0,
                  width: '220px',
                  background: '#FFF',
                  borderRadius: '15px',
                  boxShadow: '0 15px 35px rgba(0,0,0,0.2)',
                  overflow: 'hidden',
                  display: 'flex',
                  flexDirection: 'column',
                  zIndex: 2000
                }}
              >
                <div style={{ padding: '15px', borderBottom: '1px solid #EEE', fontWeight: 'bold', color: '#333' }}>
                  Account Settings
                </div>
                <button onClick={() => { setIsMenuOpen(false); onOpenProfile && onOpenProfile(); }} style={{ padding: '12px 15px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', color: '#555', fontSize: '0.9rem' }}><MapPin size={16}/> Location</button>
                <button style={{ padding: '12px 15px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', color: '#555', fontSize: '0.9rem' }}><Edit3 size={16}/> Change Name</button>
                <button style={{ padding: '12px 15px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', color: '#555', fontSize: '0.9rem' }}><Settings size={16}/> Manage Account</button>
                <button style={{ padding: '12px 15px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', color: '#555', fontSize: '0.9rem' }}><Lock size={16}/> Change Password</button>
                <button style={{ padding: '12px 15px', border: 'none', background: 'transparent', textAlign: 'left', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px', color: '#D32F2F', fontSize: '0.9rem', borderTop: '1px solid #EEE' }}><Trash2 size={16}/> Delete Account</button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.header>
  );
}
