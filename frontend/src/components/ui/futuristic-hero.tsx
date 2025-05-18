'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';

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
  const prefersReducedMotion = useReducedMotion();
  
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
  }, [cyclingWords.length]);
  
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
        <motion.div
          className="absolute top-[15%] -right-[10%] w-[30vw] h-[30vw] rounded-full bg-blue-500/10 blur-[50px]"
          style={{
            ...getParallaxStyle(0.2),
            willChange: 'transform, opacity'
          }}
          animate={
            prefersReducedMotion
              ? { opacity: 0.3 }
              : { opacity: [0.3, 0.6, 0.3] }
          }
          transition={
            prefersReducedMotion
              ? {}
              : { duration: 8, repeat: Infinity, ease: 'easeInOut' }
          }
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
      <div className="container relative z-10 flex flex-col items-center justify-center text-center pt-20 pb-12 px-4 md:pt-32 md:pb-16 md:px-6">
        <div className="max-w-4xl">
          {/* Animated title with cycling word */}
          <div className="flex flex-wrap justify-center gap-x-2 md:gap-x-3 mb-1 md:mb-2">
            {/* First part of the title */}
            {firstPartWords.map((word, i) => (
              <motion.span
                key={`first-${i}`}
                className="text-2xl sm:text-3xl md:text-4xl lg:text-6xl font-bold text-white inline-block"
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
          <div className="flex justify-center mb-1 md:mb-2 h-10 sm:h-12 md:h-16">
            <AnimatePresence mode="wait">
              <motion.span
                key={currentWordIndex}
                className="text-2xl sm:text-3xl md:text-4xl lg:text-6xl font-bold relative"
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
                  className="absolute inset-0 blur-md opacity-50 bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-600 bg-clip-text text-transparent"
                  animate={{
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
          <div className="flex flex-wrap justify-center gap-x-2 md:gap-x-3 mb-4 md:mb-6">
            {lastPartWords.map((word, i) => (
              <motion.span
                key={`last-${i}`}
                className="text-2xl sm:text-3xl md:text-4xl lg:text-6xl font-bold text-white inline-block"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ 
                  duration: 0.6, 
                  delay: 0.1 * i + firstPartWords.length * 0.1 + 0.3,
                  ease: [0.21, 0.45, 0.15, 1.0]
                }}
              >
                {word}
              </motion.span>
            ))}
          </div>
          
          {/* Subtitle */}
          <motion.p
            className="text-md sm:text-lg md:text-xl text-gray-300 max-w-3xl mx-auto mb-8 md:mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ 
              duration: 0.6, 
              delay: 0.8,
              ease: [0.21, 0.45, 0.15, 1.0]
            }}
          >
            {subtitle}
          </motion.p>
          
          {/* Buttons or CTAs */}
          <motion.div
            className="flex flex-wrap justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ 
              duration: 0.6, 
              delay: 1,
              ease: [0.21, 0.45, 0.15, 1.0]
            }}
          >
            {children}
          </motion.div>
        </div>
      </div>
      
      {/* Decorative bottom pattern */}
      <div className="absolute bottom-0 left-0 right-0 h-16 md:h-32 bg-gradient-to-t from-black to-transparent z-5" />
    </section>
  );
} 