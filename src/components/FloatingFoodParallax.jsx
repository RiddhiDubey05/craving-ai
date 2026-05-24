import { motion, useScroll, useTransform } from 'framer-motion';

export default function FloatingFoodParallax() {
  const { scrollY } = useScroll();

  // Create different scroll speeds for different layers of depth
  const y1 = useTransform(scrollY, [0, 2000], [0, -500]);
  const y2 = useTransform(scrollY, [0, 2000], [0, -800]);
  const y3 = useTransform(scrollY, [0, 2000], [0, -300]);
  
  // Rotate elements as you scroll
  const rotate1 = useTransform(scrollY, [0, 2000], [0, 360]);
  const rotate2 = useTransform(scrollY, [0, 2000], [0, -360]);

  return (
    <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 0, overflow: 'hidden' }}>
      
      {/* Layer 1: Fast floating items (Foreground) */}
      <motion.div 
        style={{ position: 'absolute', top: '20%', left: '10%', fontSize: '100px', y: y2, rotate: rotate1, filter: 'drop-shadow(0 20px 20px rgba(0,0,0,0.15))' }} 
      >🍅</motion.div>
      <motion.div 
        style={{ position: 'absolute', top: '60%', right: '15%', fontSize: '80px', y: y2, rotate: rotate2, filter: 'drop-shadow(0 20px 20px rgba(0,0,0,0.15))' }} 
      >🧄</motion.div>

      {/* Layer 2: Medium floating items (Midground) */}
      <motion.div 
        style={{ position: 'absolute', top: '40%', right: '5%', fontSize: '150px', y: y1, rotate: rotate1, opacity: 0.8, filter: 'drop-shadow(0 15px 15px rgba(0,0,0,0.1))' }} 
      >🌶️</motion.div>
      <motion.div 
        style={{ position: 'absolute', top: '80%', left: '20%', fontSize: '120px', y: y1, rotate: rotate2, opacity: 0.8, filter: 'drop-shadow(0 15px 15px rgba(0,0,0,0.1))' }} 
      >🥬</motion.div>

      {/* Layer 3: Slow floating items (Background blur) */}
      <motion.div 
        style={{ position: 'absolute', top: '30%', left: '80%', fontSize: '200px', y: y3, rotate: rotate1, opacity: 0.4, filter: 'blur(4px)' }} 
      >🍝</motion.div>
      <motion.div 
        style={{ position: 'absolute', top: '70%', right: '80%', fontSize: '150px', y: y3, rotate: rotate2, opacity: 0.4, filter: 'blur(4px)' }} 
      >🍄</motion.div>
      
    </div>
  );
}
