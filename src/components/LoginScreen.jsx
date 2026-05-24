import { useState } from 'react';
import { motion } from 'framer-motion';

export default function LoginScreen({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.05, filter: 'blur(10px)' }}
      transition={{ duration: 0.8, ease: "easeInOut" }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 1000,
        background: 'linear-gradient(135deg, #FFF6EC 0%, #FFE4C4 50%, #FFDAB9 100%)', // Warm peach/beige gradient
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        color: '#2C2C2C'
      }}
    >
      {/* Decorative Wave/Torn Paper Edge SVG in background */}
      <svg 
        style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: 'auto', zIndex: 1, pointerEvents: 'none' }} 
        viewBox="0 0 1440 320" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <path fill="#FF7A30" fillOpacity="0.1" d="M0,256L48,229.3C96,203,192,149,288,154.7C384,160,480,224,576,218.7C672,213,768,139,864,128C960,117,1056,171,1152,197.3C1248,224,1344,224,1392,224L1440,224L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path>
      </svg>

      {/* Floating abstract glowing orbs */}
      <motion.div 
        animate={{ x: [0, 50, 0], y: [0, -30, 0] }}
        transition={{ repeat: Infinity, duration: 8, ease: "easeInOut" }}
        style={{ position: 'absolute', top: '10%', left: '20%', width: '300px', height: '300px', background: '#FFC857', filter: 'blur(80px)', opacity: 0.4, borderRadius: '50%', zIndex: 1 }} 
      />
      <motion.div 
        animate={{ x: [0, -40, 0], y: [0, 40, 0] }}
        transition={{ repeat: Infinity, duration: 10, ease: "easeInOut", delay: 1 }}
        style={{ position: 'absolute', bottom: '10%', right: '20%', width: '250px', height: '250px', background: '#FF5A4E', filter: 'blur(80px)', opacity: 0.3, borderRadius: '50%', zIndex: 1 }} 
      />

      {/* Login Box */}
      <motion.div
        initial={{ y: 30, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.6, type: "spring" }}
        style={{
          background: 'rgba(255, 255, 255, 0.6)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.4)',
          borderRadius: '30px',
          padding: '50px 40px',
          width: '90%',
          maxWidth: '420px',
          boxShadow: '0 25px 50px rgba(0,0,0,0.1)',
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '35px', height: '35px', background: 'linear-gradient(135deg, #FF7A30, #FF5A4E)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: '1.2rem', boxShadow: '0 4px 10px rgba(255,122,48,0.3)' }}>
              C
            </div>
            <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#2C2C2C' }}>CravingAI.</h3>
        </div>

        <h2 style={{ fontSize: '2rem', fontWeight: '800', marginBottom: '8px', textAlign: 'center', letterSpacing: '-0.03em' }}>
          {isLogin ? 'Welcome back' : 'Join the universe'}
        </h2>
        <p style={{ color: '#666', fontSize: '1rem', marginBottom: '40px', textAlign: 'center' }}>
          {isLogin ? 'Discover your next magical meal.' : 'Create an account to start exploring.'}
        </p>

        {/* Google Auth Button */}
        <motion.button
          onClick={onLogin}
          whileHover={{ scale: 1.03, boxShadow: '0 10px 20px rgba(0,0,0,0.08)' }}
          whileTap={{ scale: 0.97 }}
          style={{
            width: '100%',
            background: 'white',
            color: '#2C2C2C',
            border: '1px solid rgba(0,0,0,0.1)',
            padding: '14px',
            borderRadius: '16px',
            fontSize: '1rem',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '12px',
            marginBottom: '25px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.02)'
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22.56 12.25C22.56 11.47 22.49 10.72 22.37 10H12V14.26H17.92C17.67 15.63 16.89 16.79 15.71 17.57V20.34H19.28C21.36 18.42 22.56 15.6 22.56 12.25Z" fill="#4285F4"/>
            <path d="M12 23C14.97 23 17.46 22.02 19.28 20.34L15.71 17.57C14.73 18.23 13.47 18.63 12 18.63C9.15 18.63 6.74 16.71 5.88 14.14H2.21V16.98C4.01 20.55 7.7 23 12 23Z" fill="#34A853"/>
            <path d="M5.88 14.14C5.66 13.48 5.53 12.76 5.53 12C5.53 11.24 5.66 10.52 5.88 9.86V7.02H2.21C1.47 8.5 1.05 10.2 1.05 12C1.05 13.8 1.47 15.5 2.21 16.98L5.88 14.14Z" fill="#FBBC05"/>
            <path d="M12 5.38C13.62 5.38 15.06 5.93 16.2 7.02L19.36 3.86C17.46 2.09 14.97 1 12 1C7.7 1 4.01 3.45 2.21 7.02L5.88 9.86C6.74 7.29 9.15 5.38 12 5.38Z" fill="#EA4335"/>
          </svg>
          Continue with Google
        </motion.button>

        <div style={{ width: '100%', display: 'flex', alignItems: 'center', margin: '15px 0' }}>
          <div style={{ flex: 1, height: '1px', background: 'rgba(0,0,0,0.1)' }}></div>
          <span style={{ padding: '0 10px', color: '#888', fontSize: '0.9rem' }}>OR</span>
          <div style={{ flex: 1, height: '1px', background: 'rgba(0,0,0,0.1)' }}></div>
        </div>

        <motion.button 
          onClick={onLogin}
          whileHover={{ scale: 1.03, boxShadow: '0 10px 20px rgba(255,122,48,0.2)' }}
          whileTap={{ scale: 0.97 }}
          style={{
            width: '100%',
            background: 'linear-gradient(135deg, #FF7A30, #FF5A4E)',
            color: 'white',
            border: 'none',
            padding: '14px',
            borderRadius: '16px',
            fontSize: '1rem',
            fontWeight: 'bold',
            cursor: 'pointer',
            boxShadow: '0 4px 15px rgba(255,122,48,0.3)',
            marginTop: '10px'
          }}
        >
          Enter as Guest
        </motion.button>

        <div style={{ marginTop: '30px', fontSize: '0.95rem', color: '#666' }}>
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <span 
            onClick={() => setIsLogin(!isLogin)}
            style={{ color: '#FF7A30', fontWeight: 'bold', cursor: 'pointer' }}
          >
            {isLogin ? 'Sign up' : 'Log in'}
          </span>
        </div>
      </motion.div>
    </motion.div>
  );
}
