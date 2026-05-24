import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Html, ContactShadows, Environment, Sphere, Cylinder, Box, Sparkles } from '@react-three/drei';
import { useRef, useState } from 'react';

function CuteChefModel({ onClick, isChatMode, isTalking }) {
  const group = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    // Gentle rotation
    group.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.2;
    if (isTalking) {
      group.current.position.y = Math.sin(state.clock.elapsedTime * 10) * 0.1 - 1;
    } else {
      group.current.position.y = -1;
    }
  });

  return (
    <group 
      ref={group} 
      onClick={!isChatMode ? onClick : undefined}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
      scale={hovered && !isChatMode ? 1.1 : 1}
      position={[0, -1, 0]}
    >
      <Float speed={isTalking ? 5 : 2} rotationIntensity={isTalking ? 1 : 0.5} floatIntensity={isTalking ? 3 : 2}>
        {/* Cooking Magic Particles */}
        {isTalking && <Sparkles count={50} scale={4} size={6} speed={2} opacity={0.8} color="#FF7A30" />}

        {/* Chef Hat */}
        <Cylinder args={[0.6, 0.8, 1, 32]} position={[0, 2.5, 0]}>
          <meshStandardMaterial color="#FFFFFF" roughness={0.1} />
        </Cylinder>
        <Sphere args={[0.9, 32, 32]} position={[0, 3, 0]}>
          <meshStandardMaterial color="#FFFFFF" roughness={0.1} />
        </Sphere>

        {/* Head */}
        <Sphere args={[1, 32, 32]} position={[0, 1.2, 0]}>
          <meshStandardMaterial color="#FFD1B3" roughness={0.4} />
        </Sphere>

        {/* Eyes */}
        <Sphere args={[0.1, 16, 16]} position={[-0.3, 1.3, 0.9]}>
          <meshStandardMaterial color="#000000" />
        </Sphere>
        <Sphere args={[0.1, 16, 16]} position={[0.3, 1.3, 0.9]}>
          <meshStandardMaterial color="#000000" />
        </Sphere>

        {/* Mustache */}
        <Box args={[0.8, 0.2, 0.2]} position={[0, 1, 0.95]} rotation={[0, 0, 0]}>
          <meshStandardMaterial color="#4A2F1D" />
        </Box>

        {/* Body (Chef Coat) */}
        <Cylinder args={[1.2, 1.5, 2, 32]} position={[0, -0.5, 0]}>
          <meshStandardMaterial color="#FFFFFF" roughness={0.3} />
        </Cylinder>

        {/* Speech Bubble using HTML overlay (Only show on Home Page) */}
        {!isChatMode && (
          <Html position={[1.5, 3.5, 0]} center zIndexRange={[10, 0]}>
            <div style={{
              background: '#FF7A30',
              color: '#FFF',
              padding: '15px 25px',
              borderRadius: '25px',
              fontWeight: '900',
              fontSize: '1.2rem',
              whiteSpace: 'nowrap',
              boxShadow: '0 10px 20px rgba(255,122,48,0.4)',
              cursor: 'pointer',
              border: '3px solid #FFF',
              transform: hovered ? 'scale(1.1)' : 'scale(1)',
              transition: 'transform 0.2s'
            }}>
              Click me to Cook! 🍳
              <div style={{ position: 'absolute', bottom: '-10px', left: '20px', width: '0', height: '0', borderLeft: '10px solid transparent', borderRight: '10px solid transparent', borderTop: '15px solid #FF7A30' }}></div>
            </div>
          </Html>
        )}
      </Float>
    </group>
  );
}

export default function CookGuide3D({ onCookChat, isChatMode = false, isTalking = false }) {
  return (
    <div style={{ width: '100%', height: '100%', minHeight: isChatMode ? '100%' : '600px', background: isChatMode ? 'transparent' : 'radial-gradient(circle at center, #FFF0E6 0%, #FFE0CC 100%)', borderRadius: '30px', position: 'relative', overflow: 'hidden', boxShadow: isChatMode ? 'none' : 'inset 0 0 50px rgba(255,122,48,0.1)' }}>
      {!isChatMode && (
        <div style={{ position: 'absolute', top: '30px', left: '30px', zIndex: 10 }}>
          <h2 style={{ fontSize: '2.5rem', color: '#FF7A30', margin: 0, fontWeight: '900', textShadow: '0 2px 10px rgba(255,122,48,0.2)' }}>Your 3D Master Chef</h2>
          <p style={{ color: '#888', fontSize: '1.1rem', marginTop: '5px', fontWeight: 'bold' }}>I will guide you step-by-step to cook anything!</p>
        </div>
      )}

      <Canvas camera={{ position: [0, 1, 6], fov: 60 }} style={{ cursor: isChatMode ? 'default' : 'pointer' }}>
        <Environment preset="studio" />
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
        
        <CuteChefModel onClick={onCookChat} isChatMode={isChatMode} isTalking={isTalking} />
        
        <ContactShadows position={[0, -2.5, 0]} opacity={0.4} scale={10} blur={2} far={4} />
      </Canvas>
    </div>
  );
}
