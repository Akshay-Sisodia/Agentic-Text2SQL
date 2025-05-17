'use client';
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface FuturisticHeroProps {
  subtitle: string;
  children?: React.ReactNode;
}

export default function FuturisticHero({
  subtitle,
  children
}: FuturisticHeroProps) {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [scrollY, setScrollY] = useState(0);
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  
  // Words to cycle through
  const cyclingWords = ["teams", "businesses", "employees", "analysts", "stakeholders"];
  
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: e.clientX / window.innerWidth,
        y: e.clientY / window.innerHeight
      });
    };
    
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('scroll', handleScroll);
    
    // Cycle through words every 2 seconds
    const wordCycleInterval = setInterval(() => {
      setCurrentWordIndex((prevIndex) => (prevIndex + 1) % cyclingWords.length);
    }, 2000);
    
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScroll);
      clearInterval(wordCycleInterval);
    };
  }, []);
  
  // Parallax calculation
  const getParallaxStyle = (depth: number) => {
    const x = (mousePosition.x * 2 - 1) * depth * 30;
    const y = (mousePosition.y * 2 - 1) * depth * 30;
    return {
      transform: `translate(${x}px, ${y}px)`,
    };
  };
  
  // Create title parts for the custom cycling title
  const titleFirstPart = "Autonomous agents transforming how";
  const titleLastPart = "interact with databases";
  
  // Split the fixed parts of the title into words for animation
  const firstPartWords = titleFirstPart.split(' ');
  const lastPartWords = titleLastPart.split(' ');
  
  // Dynamic grid pattern for background
  const Grid = () => (
    <div className="absolute inset-0 opacity-10 z-0 overflow-hidden">
      <div 
        className="w-full h-full" 
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
          transform: `translateY(${scrollY * 0.1}px)`,
        }}
      />
    </div>
  );
  
  return (
    <section className="relative min-h-screen w-full flex flex-col items-center justify-center overflow-hidden">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-gradient-to-b from-black via-purple-900/20 to-black z-0" />
      
      {/* Animated background elements */}
      <Grid />
      
      <div className="absolute inset-0 overflow-hidden">
        {/* Circles */}
        <motion.div 
          className="absolute top-[15%] -right-[10%] w-[30vw] h-[30vw] rounded-full bg-blue-500/10 blur-[50px]"
          style={getParallaxStyle(0.2)}
          animate={{
            opacity: [0.3, 0.6, 0.3],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div 
          className="absolute bottom-[10%] -left-[5%] w-[25vw] h-[25vw] rounded-full bg-indigo-500/10 blur-[40px]"
          style={getParallaxStyle(0.3)}
          animate={{
            opacity: [0.2, 0.5, 0.2],
          }}
          transition={{
            duration: 7,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 1
          }}
        />
        <motion.div 
          className="absolute top-[40%] left-[60%] w-[15vw] h-[15vw] rounded-full bg-purple-500/10 blur-[60px]"
          style={getParallaxStyle(0.5)}
          animate={{
            opacity: [0.2, 0.4, 0.2],
          }}
          transition={{
            duration: 9,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 2
          }}
        />
        
        {/* Light rays */}
        <motion.div 
          className="absolute inset-0 opacity-30"
          style={{
            background: 'radial-gradient(ellipse at 50% 50%, rgba(138, 43, 226, 0.2), transparent 70%)',
          }}
          animate={{
            opacity: [0.2, 0.3, 0.2],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>
      
      {/* Content */}
      <div className="container relative z-10 flex flex-col items-center justify-center text-center pt-32 pb-16 md:pt-24 md:pb-20">
        <div className="max-w-4xl">
          {/* Animated title with cycling word */}
          <div className="flex flex-wrap justify-center gap-x-3 mb-2">
            {/* First part of the title */}
            {firstPartWords.map((word, i) => (
              <motion.span
                key={`first-${i}`}
                className="text-4xl md:text-5xl lg:text-6xl font-bold text-white inline-block"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ 
                  duration: 0.6, 
                  delay: 0.1 * i,
                  ease: [0.21, 0.45, 0.15, 1.0]
                }}
              >
                {word}
              </motion.span>
            ))}
          </div>
          
          {/* The cycling word with animation */}
          <div className="flex justify-center mb-2 h-16">
            <AnimatePresence mode="wait">
              <motion.span
                key={currentWordIndex}
                className="text-4xl md:text-5xl lg:text-6xl font-bold relative"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
              >
                <motion.span 
                  className="bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-600 bg-clip-text text-transparent"
                  animate={{
                    backgroundPosition: ['0% center', '100% center', '0% center'],
                    scale: [1, 1.05, 1]
                  }}
                  transition={{
                    duration: 3,
                    ease: "easeInOut",
                    times: [0, 0.5, 1],
                    repeat: Infinity,
                  }}
                  style={{
                    backgroundSize: "200% auto"
                  }}
                >
                  {cyclingWords[currentWordIndex]}
                </motion.span>
                {/* Glow effect */}
                <motion.span
                  className="absolute inset-0 blur-md opacity-40 bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-600 bg-clip-text text-transparent"
                  animate={{
                    opacity: [0.4, 0.7, 0.4],
                    backgroundPosition: ['0% center', '100% center', '0% center'],
                  }}
                  transition={{
                    duration: 3,
                    ease: "easeInOut",
                    times: [0, 0.5, 1],
                    repeat: Infinity,
                  }}
                  style={{
                    backgroundSize: "200% auto"
                  }}
                >
                  {cyclingWords[currentWordIndex]}
                </motion.span>
              </motion.span>
            </AnimatePresence>
          </div>
          
          {/* Last part of the title */}
          <div className="flex flex-wrap justify-center gap-x-3 mb-6">
            {lastPartWords.map((word, i) => (
              <motion.span
                key={`last-${i}`}
                className="text-4xl md:text-5xl lg:text-6xl font-bold text-white inline-block"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ 
                  duration: 0.6, 
                  delay: 0.1 * (i + firstPartWords.length + 1),
                  ease: [0.21, 0.45, 0.15, 1.0]
                }}
              >
                {word}
              </motion.span>
            ))}
          </div>
          
          {/* Subtitle */}
          <motion.p 
            className="text-lg md:text-xl text-white/70 mb-8 max-w-2xl mx-auto"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            {subtitle}
          </motion.p>
          
          {/* Buttons */}
          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            {children}
          </motion.div>
        </div>
      </div>
    </section>
  );
} 