"use client";

import React from "react";
import { useEffect, useRef, useState } from "react";
import { motion, useAnimation } from "framer-motion";
import { debounce, throttle } from "lodash";
import { cn } from "../../lib/utils";

interface BackgroundRippleEffectProps {
  className?: string;
}

function BackgroundRippleEffect({ className }: BackgroundRippleEffectProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const controls = useAnimation();

  // Update dimensions on mount and resize
  useEffect(() => {
    if (containerRef.current) {
      const updateDimensions = () => {
        const { width, height } = containerRef.current?.getBoundingClientRect() || { width: 0, height: 0 };
        setDimensions({ width, height });
      };

      const debouncedUpdateDimensions = debounce(updateDimensions, 200);
      
      updateDimensions();
      window.addEventListener("resize", debouncedUpdateDimensions);
      return () => window.removeEventListener("resize", debouncedUpdateDimensions);
    }
  }, []);

  // Handle mouse movement
  useEffect(() => {
    const throttledAnimate = throttle((x: number, y: number) => {
      controls.start({
        opacity: [0.2, 0.1, 0],
        scale: [1, 2, 3],
        transition: { duration: 2 }
      });
    }, 50); // Throttle to 50ms

    const handleMouseMove = (e: MouseEvent) => {
      if (containerRef.current) {
        const { left, top } = containerRef.current.getBoundingClientRect();
        setMousePosition({ 
          x: e.clientX - left, 
          y: e.clientY - top 
        });
        
        // Animate the ripple
        throttledAnimate(e.clientX - left, e.clientY - top);
      }
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [controls]);

  // Calculate grid cell size and count
  const cellSize = 60; // Size of each grid cell
  const cols = Math.ceil(dimensions.width / cellSize) + 1;
  const rows = Math.ceil(dimensions.height / cellSize) + 1;
  const maxDistance = 400; // Maximum distance for glow effect

  // Grid cell component for optimization
  const GridCell = React.memo(({ 
    rowIndex, 
    colIndex, 
    cellSize, 
    mousePosition, 
    maxDistance 
  }: {
    rowIndex: number;
    colIndex: number;
    cellSize: number;
    mousePosition: { x: number; y: number };
    maxDistance: number;
  }) => {
    const x = colIndex * cellSize;
    const y = rowIndex * cellSize;
    
    const distance = Math.sqrt(
      Math.pow(mousePosition.x - (x + cellSize / 2), 2) +
      Math.pow(mousePosition.y - (y + cellSize / 2), 2)
    );
    
    const proximity = Math.max(0, 1 - distance / maxDistance);
    
    return (
      <motion.div
        className="border border-gray-800/30"
        style={{ 
          width: cellSize, 
          height: cellSize,
          backgroundColor: `rgba(98, 58, 162, ${proximity * 0.1})` 
        }}
        animate={{
          backgroundColor: [
            `rgba(98, 58, 162, ${proximity * 0.1})`,
            `rgba(61, 65, 175, ${proximity * 0.2})`,
            `rgba(98, 58, 162, ${proximity * 0.1})`
          ]
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          repeatType: "reverse",
          ease: "easeInOut",
          delay: (rowIndex + colIndex) * 0.05 % 1
        }}
      />
    );
  });

  return (
    <div
      ref={containerRef}
      className={cn(
        "fixed inset-0 z-0 overflow-hidden bg-black pointer-events-none",
        className
      )}
    >
      {/* Grid pattern */}
      <div className="absolute inset-0">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={`row-${rowIndex}`} className="flex">
            {Array.from({ length: cols }).map((_, colIndex) => (
              <GridCell
                key={`cell-${rowIndex}-${colIndex}`}
                rowIndex={rowIndex}
                colIndex={colIndex}
                cellSize={cellSize}
                mousePosition={mousePosition}
                maxDistance={maxDistance}
              />
            ))}
          </div>
        ))}
      </div>

      {/* Ripple effect on mouse move */}
      <motion.div
        className="absolute w-40 h-40 rounded-full"
        style={{
          left: mousePosition.x - 80,
          top: mousePosition.y - 80,
          background: "radial-gradient(circle, rgba(138, 78, 222, 0.3) 0%, rgba(61, 65, 175, 0) 70%)"
        }}
        animate={controls}
      />

      {/* Static background gradients */}
      <div className="absolute top-0 left-0 right-0 h-screen w-screen overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-purple-500/20 rounded-full filter blur-3xl" />
        <div className="absolute top-1/3 -right-40 w-96 h-96 bg-blue-500/20 rounded-full filter blur-3xl" />
        <div className="absolute -bottom-20 left-1/3 w-96 h-96 bg-indigo-500/20 rounded-full filter blur-3xl" />
      </div>
    </div>
  );
}

export { BackgroundRippleEffect };
export default BackgroundRippleEffect; 