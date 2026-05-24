import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Environment, Cloud, Stars } from '@react-three/drei';
import * as THREE from 'three';

function AtmosphericFog({ theme }) {
  const fogColor = theme === 'day' ? '#FFF6EC' : '#0A1128';
  return <fog attach="fog" args={[fogColor, 5, 20]} />;
}

function FloatingParticles({ theme }) {
  const points = useRef();
  
  // Create 100 random particles
  const particleCount = 100;
  const positions = new Float32Array(particleCount * 3);
  for(let i=0; i<particleCount*3; i++) {
    positions[i] = (Math.random() - 0.5) * 20;
  }

  useFrame((state, delta) => {
    if (points.current) {
      points.current.rotation.y += delta * 0.05;
      points.current.rotation.x += delta * 0.02;
    }
  });

  const color = theme === 'day' ? '#FF7A30' : '#FFC857';

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particleCount}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial 
        size={0.1} 
        color={color} 
        transparent 
        opacity={0.6}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

export default function CinematicBackground({ theme }) {
  return (
    <div className="cinematic-canvas">
      <Canvas camera={{ position: [0, 0, 10], fov: 60 }}>
        <AtmosphericFog theme={theme} />
        
        {theme === 'night' && <Stars radius={100} depth={50} count={2000} factor={4} saturation={0} fade speed={1} />}
        
        <ambientLight intensity={theme === 'day' ? 1.5 : 0.2} />
        <directionalLight 
          position={[5, 5, 5]} 
          intensity={theme === 'day' ? 2 : 0.5} 
          color={theme === 'day' ? '#FFC857' : '#5A75FF'} 
        />

        {/* Soft volumetric clouds acting as the "depth fog" */}
        <Cloud 
          opacity={0.3} 
          speed={0.4} 
          width={20} 
          depth={2} 
          segments={20} 
          position={[0, -2, -5]} 
          color={theme === 'day' ? '#FFF6EC' : '#1A2138'}
        />

        <FloatingParticles theme={theme} />
      </Canvas>
    </div>
  );
}
