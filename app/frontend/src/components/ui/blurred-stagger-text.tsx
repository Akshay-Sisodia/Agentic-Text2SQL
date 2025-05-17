"use client" 

import * as React from "react"
import { motion, useAnimation } from "framer-motion";
import { cn } from "../../lib/utils";
 
export const BlurredStagger = ({
  text = "we love hextaui.com ❤️",
  style = {},
  fontSize = { xs: '1.75rem', md: '2.75rem' },
  isVisible = true,
  className
}: {
  text: string;
  style?: React.CSSProperties;
  fontSize?: { xs: string; md: string; };
  isVisible?: boolean;
  className?: string;
}) => {
  const headingText = text;
  const controls = useAnimation();
  const [key, setKey] = React.useState(0);

  // Trigger animation when isVisible changes
  React.useEffect(() => {
    if (isVisible) {
      setKey(prev => prev + 1); // Force re-render to restart animation
      controls.start("show");
    } else {
      controls.start("hidden");
    }
  }, [isVisible, controls]);
 
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.03,
        delayChildren: 0.1,
      },
    },
  };
 
  const letterAnimation = {
    hidden: {
      opacity: 0,
      filter: "blur(15px)",
      y: 10,
      scale: 0.9,
    },
    show: {
      opacity: 1,
      filter: "blur(0px)",
      y: 0,
      scale: 1,
      transition: {
        duration: 0.5, 
        ease: [0.43, 0.13, 0.23, 0.96], // Custom easing for more dramatic effect
      }
    },
  };
 
  return (
    <div 
      className={cn(
        "relative inline-block mb-2 overflow-visible max-w-full",
        className
      )}
      style={{ 
        ...style,
        fontSize: typeof window !== 'undefined' && window.innerWidth < 768 ? fontSize.xs : fontSize.md,
        fontWeight: 700,
      }}
    >
      <motion.div
        key={key}
        variants={container}
        initial="hidden"
        animate={controls}
        style={{ 
          display: 'inline-block',
          position: 'relative'
        }}
      >
        {headingText.split("").map((char, index) => (
          <motion.span
            key={`${char}-${index}-${key}`} // Ensure unique key for each animation cycle
            variants={letterAnimation}
            style={{
              display: 'inline-block',
              backgroundImage: 'linear-gradient(90deg, #f8fafc 0%, #6366f1 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              textShadow: '0 0 8px rgba(99, 102, 241, 0.3)',
            }}
          >
            {char === " " ? "\u00A0" : char}
          </motion.span>
        ))}
      </motion.div>
    </div>
  );
}; 