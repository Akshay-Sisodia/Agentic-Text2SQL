import React, { useState, useEffect } from 'react';
import { cn } from "../lib/utils";
import type { ElementType } from 'react';

interface AnimatedTextCycleProps {
  words: string[];
  interval?: number;
  variant?: "h1" | "h2" | "h3" | "h4" | "h5" | "h6";
  sx?: React.CSSProperties;
  className?: string;
  reverse?: boolean;
  component?: ElementType;
}

const AnimatedTextCycle: React.FC<AnimatedTextCycleProps> = ({ 
  words, 
  interval = 2000,
  variant = "h2",
  sx = {},
  className,
  reverse = false,
  component
}) => {
  const [currentIndex, setCurrentIndex] = useState(reverse ? words.length - 1 : 0);
  const [isChanging, setIsChanging] = useState(false);

  useEffect(() => {
    const wordInterval = setInterval(() => {
      setIsChanging(true);
      setTimeout(() => {
        setCurrentIndex((prevIndex) => {
          if (reverse) {
            // Move backward through the array
            return prevIndex === 0 ? words.length - 1 : prevIndex - 1;
          } else {
            // Move forward through the array (original behavior)
            return (prevIndex + 1) % words.length;
          }
        });
        setIsChanging(false);
      }, 300); // Fade out time
    }, interval);

    return () => clearInterval(wordInterval);
  }, [words.length, interval, reverse]);

  const variantClasses = {
    h1: "text-4xl md:text-6xl font-bold",
    h2: "text-3xl md:text-5xl font-semibold",
    h3: "text-2xl md:text-4xl font-semibold",
    h4: "text-xl md:text-3xl font-semibold",
    h5: "text-lg md:text-2xl font-semibold",
    h6: "text-base md:text-xl font-semibold",
  }[variant] || "text-2xl md:text-4xl font-semibold";

  // Use the component prop if provided, otherwise use the variant
  const Component = component || (variant as ElementType) || 'div';

  return (
    <Component
      className={cn(
        variantClasses,
        "inline-block transition-opacity duration-300 ease-in-out animate-shimmer bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 to-blue-500 to-indigo-500 bg-[length:400%_100%] bg-clip-text text-transparent",
        isChanging ? "opacity-0 translate-y-5" : "opacity-100 translate-y-0",
        className
      )}
      style={{
        ...sx,
        textShadow: '0 0 10px rgba(99, 102, 241, 0.3)',
        fontWeight: 600,
      }}
    >
      {words[currentIndex]}
    </Component>
  );
};

export default AnimatedTextCycle; 