import { cn } from "../../lib/utils"
import { TestimonialCard } from "./testimonial-card"
import type { TestimonialAuthor } from "./testimonial-card"
import { motion } from "framer-motion"
import { useRef, useEffect, useState } from "react"
import BackgroundRippleEffect from "./background-ripple-effect"

interface TestimonialsSectionProps {
  title: string
  description: string
  testimonials: Array<{
    author: TestimonialAuthor
    text: string
    href?: string
  }>
  className?: string
}

export function TestimonialsSection({ 
  title,
  description,
  testimonials,
  className 
}: TestimonialsSectionProps) {
  const marqueeRef = useRef<HTMLDivElement>(null);
  const [isPaused, setIsPaused] = useState(false);
  
  // Measure the width of the marquee content for a more accurate animation

  
  return (
    <section className={cn(
      "relative overflow-hidden",
      "pt-6 pb-12 md:pt-8 md:pb-20",
      className
    )}>
      {/* Integrated background effect component */}
      <div className="absolute inset-0 z-0">
        <BackgroundRippleEffect className="opacity-70" />
      </div>
      
      {/* Decorative elements */}
      <div className="absolute inset-0 pointer-events-none z-10">
        <div className="absolute top-20 left-[5%] w-48 md:w-72 h-48 md:h-72 bg-purple-500/10 rounded-full filter blur-3xl" />
        <div className="absolute bottom-40 right-[10%] w-48 md:w-72 h-48 md:h-72 bg-blue-500/10 rounded-full filter blur-3xl" />
      </div>
      
      <div className="container mx-auto max-w-7xl flex flex-col items-center gap-6 md:gap-12 px-4 relative z-20">
        <motion.div 
          className="text-center mb-4 md:mb-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          style={{ position: 'relative' }}
        >
          <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-600 bg-clip-text text-transparent mb-3 sm:mb-6">
            {title}
          </h2>
          <p className="text-sm md:text-md max-w-[600px] mx-auto text-white/70 sm:text-lg">
            {description}
          </p>
        </motion.div>
        
        <div className="relative w-full overflow-hidden">
          {/* Main marquee container */}
          <motion.div 
            className="flex w-full"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            {/* Single marquee row with pause on hover */}
            <div 
              className="flex overflow-hidden [--duration:40s] [--gap:1rem] md:[--gap:1.5rem] hover-pause-container"
              onMouseEnter={() => setIsPaused(true)}
              onMouseLeave={() => setIsPaused(false)}
 style={{
   "--pause-state": isPaused ? "paused" : "running"
 } as React.CSSProperties & { '--pause-state': string }}
            >
              <div 
                ref={marqueeRef}
                className="flex items-center [gap:var(--gap)] py-2 md:py-4 pl-2 md:pl-4 animate-marquee"
                style={{ 
                  willChange: "transform",
                  animationPlayState: "var(--pause-state)"
                }}
              >
                {/* Duplicate testimonials multiple times for seamless loop */}
 {/* Only duplicate if needed for sufficient marquee content */}
 {(testimonials.length < 5 ? [...Array(2)] : [0]).map((_, dupIndex) => (
   testimonials.map((testimonial, i) => (
     <TestimonialCard 
       key={`first-${dupIndex}-${i}`}
       {...testimonial}
       className="border border-white/10 min-w-[230px] xs:min-w-[260px] sm:min-w-[280px] md:min-w-[320px] flex-shrink-0"
     />
   ))
 ))}
              </div>
              
              {/* Clone of first marquee for seamless loop */}
              <div 
                aria-hidden="true"
                className="flex items-center [gap:var(--gap)] py-2 md:py-4 pl-2 md:pl-4 animate-marquee"
                style={{ 
                  willChange: "transform",
                  animationPlayState: "var(--pause-state)"
                }}
              >
                {/* Duplicate testimonials multiple times for seamless loop */}
                {[...Array(2)].map((_, dupIndex) => (
                  testimonials.map((testimonial, i) => (
                    <TestimonialCard 
                      key={`second-${dupIndex}-${i}`}
                      {...testimonial}
                      className="border border-white/10 min-w-[230px] xs:min-w-[260px] sm:min-w-[280px] md:min-w-[320px] flex-shrink-0"
                    />
                  ))
                ))}
              </div>
            </div>
          </motion.div>
          
          {/* Edge fading gradients */}
          <div className="pointer-events-none absolute inset-y-0 left-0 w-[10%] bg-gradient-to-r from-black" />
          <div className="pointer-events-none absolute inset-y-0 right-0 w-[10%] bg-gradient-to-l from-black" />
        </div>
      </div>
    </section>
  )
} 