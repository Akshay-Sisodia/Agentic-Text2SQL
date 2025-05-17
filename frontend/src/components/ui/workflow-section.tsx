'use client';
import { useRef, useEffect } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { LucideBrain, LucideDatabase, LucideSearchCheck, LucideTable2, LucideCode } from 'lucide-react';

export default function WorkflowSection() {
  // Animation references and values
  const containerRef = useRef<HTMLElement>(null);
  const pathRef = useRef<SVGPathElement>(null);
  
  // Get path length on component mount for accurate animations
  useEffect(() => {
    if (pathRef.current) {
      // We still need to calculate the path length for animation
      const pathTotalLength = pathRef.current.getTotalLength();
      pathRef.current.style.strokeDasharray = `${pathTotalLength} ${pathTotalLength}`;
      pathRef.current.style.strokeDashoffset = `${pathTotalLength}`;
    }
  }, []);
  
  // Scroll-based animation for the path
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"]
  });
  
  // Create a smoother animation by spring-loading the scroll value
  const smoothPathLength = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });
  
  // Transform the scroll progress to path drawing progress - adjusted to start earlier
  const pathDrawProgress = useTransform(smoothPathLength, [0.01, 0.8], [0, 1]);
  
  const flowSteps = [
    {
      icon: LucideBrain,
      title: "IntentAgent",
      processName: "Natural Language Understanding",
      description: "Interprets natural language to extract intent and key query elements.",
      color: "from-blue-500 to-indigo-600",
      glowColor: "rgba(93, 63, 211, 0.3)",
      input: "Show me sales by region for the last quarter where revenue exceeds $10,000",
      output: "Intent: Sales aggregation | Entities: sales, region, revenue | Time: last quarter | Filter: revenue > $10k | Group by: region",
      explanation: "Extracts meaning, entities, and conditions from your natural language query."
    },
    {
      icon: LucideSearchCheck,
      title: "SchemaMapperAgent",
      processName: "Schema Mapping",
      description: "Maps query elements to your specific database structure.",
      color: "from-indigo-500 to-purple-600",
      glowColor: "rgba(129, 86, 245, 0.3)",
      input: "Query elements: sales, regions, revenue, date filters",
      output: "Tables: sales, regions | Join: sales.region_id → regions.id | Time calc: Last quarter (3 months)",
      explanation: "Identifies relevant tables and relationships in your database schema."
    },
    {
      icon: LucideCode,
      title: "SQLAgent",
      processName: "SQL Generation",
      description: "Creates optimized SQL with proper structure and syntax.",
      color: "from-purple-500 to-fuchsia-600",
      glowColor: "rgba(192, 38, 211, 0.3)",
      input: "Schema mapping with sales and regions tables",
      output: `SELECT r.region_name, SUM(s.revenue) as total_revenue
FROM sales s
JOIN regions r ON s.region_id = r.id
WHERE s.date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
AND s.revenue > 10000
GROUP BY r.region_name
ORDER BY total_revenue DESC;`,
      explanation: "Constructs SQL with proper JOINs, filters, and aggregations."
    },
    {
      icon: LucideDatabase,
      title: "QueryExecutor",
      processName: "Query Execution",
      description: "Runs the query securely against your database.",
      color: "from-fuchsia-500 to-pink-600",
      glowColor: "rgba(217, 70, 239, 0.3)",
      input: "Optimized SQL query",
      output: "tableView",
      executionMetrics: {
        time: "0.34s",
        rows: "4",
        optimizations: "Index scans, Join optimization"
      },
      explanation: "Executes query efficiently using database indexes and optimizations."
    },
    {
      icon: LucideTable2,
      title: "ExplanationAgent",
      processName: "SQL Explanation",
      description: "Explains the SQL query in clear, human-friendly terms.",
      color: "from-pink-500 to-rose-600",
      glowColor: "rgba(236, 72, 153, 0.3)",
      input: "Generated SQL query and execution results",
      output: "This query joins the sales and regions tables to calculate total revenue by region for the last quarter. It filters for sales exceeding $10,000, groups by region name, and sorts results in descending order by revenue. The JOIN operation connects sales data with region names using the region_id foreign key relationship.",
      explanation: "Translates complex SQL operations into easy-to-understand explanations."
    }
  ];

  return (
    <section 
      className="relative py-24 overflow-hidden" 
      id="how-it-works" 
      ref={containerRef} 
      style={{ position: "relative" }}
    >
      {/* Enhanced Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-b from-black via-purple-900/10 to-black -z-10" />
      
      {/* Enhanced grid pattern with subtle animation */}
      <div className="absolute inset-0 opacity-10 -z-5">
        <motion.div 
          className="w-full h-full" 
          style={{
            backgroundImage: `
              linear-gradient(to right, rgba(139, 92, 246, 0.15) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(139, 92, 246, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '60px 60px',
          }}
          animate={{ 
            backgroundPosition: ['0px 0px', '60px 60px'],
            opacity: [0.1, 0.13, 0.1]
          }}
          transition={{ 
            duration: 20,
            ease: "linear",
            repeat: Infinity,
            repeatType: "reverse"
          }}
        />
      </div>
      
      <div className="container mx-auto z-10 relative">
        {/* Section Header with enhanced animation */}
        <motion.div 
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="font-heading text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent mb-4">
            How It Works
          </h2>
          <p className="text-xl text-white/70 max-w-3xl mx-auto">
            See how Agentic Text2SQL transforms your natural language questions into powerful SQL queries
          </p>
        </motion.div>

        {/* Initial Query Box with enhanced glow effect */}
        <motion.div
          className="max-w-5xl mx-auto mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
        >
          <div className="relative bg-gradient-to-br from-gray-900/80 to-gray-800/60 rounded-xl p-8 border border-white/10 backdrop-blur-sm shadow-xl overflow-hidden">
            {/* Background glow effect */}
            <div className="absolute -inset-1 bg-gradient-to-r from-purple-600/20 via-transparent to-blue-600/20 blur-xl opacity-50"></div>
            
            <h3 className="text-2xl text-white/90 font-semibold mb-4 relative z-10">Your Question:</h3>
            <div className="relative bg-gray-950/70 rounded-lg p-6 font-mono text-green-400 text-lg md:text-xl z-10">
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                "Show me sales by region for the last quarter where revenue exceeds $10,000"
              </motion.span>
            </div>
          </div>
        </motion.div>

        {/* Enhanced Flowing Path Timeline */}
        <div className="relative mx-auto overflow-visible">
          {/* SVG Path Container - This holds our flowing path */}
          <div className="absolute left-1/2 -translate-x-1/2 w-[10px] h-full pointer-events-none overflow-visible">
            <svg 
              className="absolute h-full w-full overflow-visible" 
              viewBox="0 0 100 1000" 
              preserveAspectRatio="none"
              style={{ 
                top: '0', 
                height: '100%',
                left: '-45px',
                width: '100px'
              }}
            >
              {/* Enhanced defs with multiple gradients and filters */}
              <defs>
                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="25%" stopColor="#8b5cf6" />
                  <stop offset="50%" stopColor="#a855f7" />
                  <stop offset="75%" stopColor="#d946ef" />
                  <stop offset="100%" stopColor="#ec4899" />
                </linearGradient>
                
                <linearGradient id="connectorGradient-right" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
                </linearGradient>
                
                <linearGradient id="connectorGradient-left" x1="100%" y1="0%" x2="0%" y2="0%">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
                </linearGradient>

                {/* Enhanced glow effect with multiple layers */}
                <filter id="enhanced-glow" x="-50%" y="-50%" width="200%" height="200%">
                  <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur" />
                  <feFlood floodColor="#8b5cf6" floodOpacity="0.7" result="color"/>
                  <feComposite in="color" in2="blur" operator="in" result="glow"/>
                  <feMerge>
                    <feMergeNode in="glow" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
                
                <filter id="connector-glow" x="-100%" y="-100%" width="300%" height="300%">
                  <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
                  <feFlood floodColor="#8b5cf6" floodOpacity="0.6" result="glow"/>
                  <feComposite in="glow" in2="blur" operator="in" result="glow"/>
                  <feMerge>
                    <feMergeNode in="glow" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>

                {/* Particle filter */}
                <filter id="particle-glow" x="-100%" y="-100%" width="300%" height="300%">
                  <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
                  <feFlood floodColor="#ffffff" floodOpacity="1" result="white-glow"/>
                  <feComposite in="white-glow" in2="blur" operator="in" result="white-glow"/>
                  <feMerge>
                    <feMergeNode in="white-glow" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
                
              {/* The main flowing path with scroll-based animation */}
              <motion.path
                ref={pathRef}
                d="M50,0 C70,100 30,200 50,300 C70,400 30,500 50,600 C70,700 30,800 50,900"
                fill="none"
                stroke="url(#lineGradient)"
                strokeWidth="8"
                strokeLinecap="round"
                filter="url(#enhanced-glow)"
                style={{ pathLength: pathDrawProgress }}
              />
            </svg>
          </div>
          
          {/* The actual content steps with improved design - now using scroll progress */}
          <div className="relative z-10">
            {flowSteps.map((step, index) => {
              const StepContent = () => {
                const ref = useRef<HTMLDivElement>(null);
                
                // Calculate scroll-based thresholds for this step - adjusted to start earlier
                const stepStartProgress = 0.05 + (index * 0.14);
                const stepEndProgress = stepStartProgress + 0.16;
                
                // Map scroll progress to this step's visibility - modified to keep stages visible after completion
                const stepOpacity = useTransform(
                  smoothPathLength,
                  [stepStartProgress - 0.05, stepStartProgress, stepEndProgress],
                  [0, 1, 1]
                );
                
                // Y position transformation - modified to keep stages in place after completion
                const stepY = useTransform(
                  smoothPathLength,
                  [stepStartProgress - 0.05, stepStartProgress],
                  [20, 0]
                );
                
                // Calculate position to make it appear on alternating sides of the path
                const isRight = index % 2 === 0;
                
                return (
                  <div className="py-28 first:py-12 last:pb-8" ref={ref}>
                    <div className={`flex items-center ${isRight ? 'justify-end md:mr-[calc(50%-180px)]' : 'justify-start md:ml-[calc(50%-180px)]'}`}>
                      <motion.div 
                        className={`relative md:max-w-[60%] ${isRight ? 'md:mr-16' : 'md:ml-16'} w-full max-w-[95%] mx-auto md:mx-0`}
                        style={{
                          opacity: stepOpacity,
                          y: stepY
                        }}
                      >
                        {/* Enhanced step content card with more dynamic effects */}
                        <motion.div 
                          className="relative bg-black/60 rounded-2xl border border-white/10 backdrop-blur-sm shadow-lg overflow-hidden"
                          whileHover={{ 
                            y: -5,
                            boxShadow: `0 15px 30px -10px ${step.glowColor}` 
                          }}
                          style={{ 
                            boxShadow: `0 5px 20px -5px ${step.glowColor}`,
                          }}
                        >
                          {/* Animated gradient background */}
                          <motion.div 
                            className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${step.color} opacity-10`}
                            animate={{ 
                              opacity: [0.05, 0.15, 0.05],
                              backgroundPosition: ['0% 0%', '100% 100%']
                            }}
                            transition={{ 
                              duration: 10,
                              repeat: Infinity,
                              repeatType: "reverse"
                            }}
                          />
                          
                          <div className="p-8 relative z-10">
                            {/* Step Icon and Title Section */}
                            <div className="flex items-center gap-5 mb-5">
                              <motion.div 
                                className={`w-14 h-14 rounded-lg flex items-center justify-center bg-gradient-to-br ${step.color} shadow-lg`}
                                style={{ boxShadow: `0 0 15px ${step.glowColor}` }}
                                whileHover={{ 
                                  scale: 1.1,
                                  boxShadow: `0 0 20px ${step.glowColor}`
                                }}
                              >
                                <step.icon className="w-7 h-7 text-white" />
                              </motion.div>
                              <div>
                                <div className="flex items-center">
                                  <span className={`bg-gradient-to-r ${step.color} text-transparent bg-clip-text text-2xl font-bold mr-2`}>0{index + 1}</span>
                                  <h3 className={`font-heading text-2xl font-bold bg-gradient-to-r ${step.color} bg-clip-text text-transparent`}>
                                    {step.title}
                                  </h3>
                                </div>
                                <p className="text-white/80 text-base mt-2">
                                  {step.description}
                                </p>
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-1 gap-5 mt-6">
                              {/* Input with enhanced styling */}
                              <motion.div 
                                className="bg-black/70 rounded-lg p-5 border border-white/10"
                                style={{
                                  opacity: useTransform(
                                    smoothPathLength,
                                    [stepStartProgress, stepStartProgress + 0.04],
                                    [0, 1]
                                  ),
                                  y: useTransform(
                                    smoothPathLength,
                                    [stepStartProgress, stepStartProgress + 0.04],
                                    [10, 0]
                                  )
                                }}
                              >
                                <h4 className="text-white/90 font-semibold text-xs uppercase tracking-wider mb-2">
                                  Input
                                </h4>
                                <div className="font-mono text-blue-300 text-sm overflow-x-auto max-h-32 overflow-y-auto scrollbar-thin scrollbar-track-black/20 scrollbar-thumb-blue-700/50">
                                  {typeof step.input === 'string' ? (
                                    <div className="whitespace-pre-wrap">{step.input}</div>
                                  ) : (
                                    <pre className="whitespace-pre-wrap">{JSON.stringify(step.input, null, 2)}</pre>
                                  )}
                                </div>
                              </motion.div>
                              
                              {/* Output with enhanced styling */}
                              <motion.div 
                                className="bg-black/70 rounded-lg p-5 border border-white/10"
                                style={{
                                  opacity: useTransform(
                                    smoothPathLength,
                                    [stepStartProgress + 0.02, stepStartProgress + 0.06],
                                    [0, 1]
                                  ),
                                  y: useTransform(
                                    smoothPathLength,
                                    [stepStartProgress + 0.02, stepStartProgress + 0.06],
                                    [10, 0]
                                  )
                                }}
                              >
                                <h4 className="text-white/90 font-semibold text-xs uppercase tracking-wider mb-2">
                                  Output
                                </h4>
                                <div className="font-mono text-green-300 text-sm overflow-x-auto max-h-48 overflow-y-auto scrollbar-thin scrollbar-track-black/20 scrollbar-thumb-green-700/50">
                                  {step.output === 'tableView' ? (
                                    <div>
                                      <table className="min-w-full text-sm">
                                        <thead>
                                          <tr className="border-b border-white/10">
                                            <th className="text-left py-1 px-2 text-white/90">Region</th>
                                            <th className="text-left py-1 px-2 text-white/90">Total Revenue</th>
                                          </tr>
                                        </thead>
                                        <tbody>
                                          <tr className="border-b border-white/5">
                                            <td className="py-1 px-2 text-white/80">North America</td>
                                            <td className="py-1 px-2 text-green-400">$342,876.50</td>
                                          </tr>
                                          <tr className="border-b border-white/5">
                                            <td className="py-1 px-2 text-white/80">Europe</td>
                                            <td className="py-1 px-2 text-green-400">$295,432.18</td>
                                          </tr>
                                          <tr className="border-b border-white/5">
                                            <td className="py-1 px-2 text-white/80">Asia Pacific</td>
                                            <td className="py-1 px-2 text-green-400">$187,654.32</td>
                                          </tr>
                                          <tr>
                                            <td className="py-1 px-2 text-white/80">Latin America</td>
                                            <td className="py-1 px-2 text-green-400">$98,756.75</td>
                                          </tr>
                                        </tbody>
                                      </table>
                                      {step.executionMetrics && (
                                        <div className="mt-3 pt-3 border-t border-white/10 text-xs text-white/60 flex flex-wrap gap-4">
                                          <div>
                                            <span className="font-semibold text-white/80">Time:</span> {step.executionMetrics.time}
                                          </div>
                                          <div>
                                            <span className="font-semibold text-white/80">Rows:</span> {step.executionMetrics.rows}
                                          </div>
                                          <div>
                                            <span className="font-semibold text-white/80">Optimizations:</span> {step.executionMetrics.optimizations}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  ) : typeof step.output === 'string' ? (
                                    <div className="whitespace-pre-wrap">{step.output}</div>
                                  ) : (
                                    <pre className="whitespace-pre-wrap">{JSON.stringify(step.output, null, 2)}</pre>
                                  )}
                                </div>
                              </motion.div>
                            </div>
                          </div>
                        </motion.div>
                      </motion.div>
                    </div>
                  </div>
                );
              };
              
              return <StepContent key={index} />;
            })}
          </div>
          
          {/* Final Result Box with enhanced effects */}
          <motion.div
            className="max-w-5xl mx-auto mt-16"
            style={{
              opacity: useTransform(smoothPathLength, [0.75, 0.85], [0, 1]),
              y: useTransform(smoothPathLength, [0.75, 0.85], [20, 0])
            }}
          >
            <div className="relative bg-gradient-to-br from-purple-900/30 to-indigo-900/30 rounded-xl p-8 border border-white/10 backdrop-blur-sm shadow-xl overflow-hidden">
              {/* Animated background glow */}
              <motion.div 
                className="absolute -inset-1 bg-gradient-to-r from-purple-600/20 via-transparent to-blue-600/20 blur-xl" 
                animate={{ 
                  opacity: [0.2, 0.4, 0.2],
                  rotate: [0, 15],
                }}
                transition={{ 
                  duration: 8, 
                  repeat: Infinity, 
                  repeatType: "reverse" 
                }}
              />
              
              <div className="text-center mb-8 relative z-10">
                <motion.h3 
                  className="font-heading text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent"
                  animate={{ 
                    backgroundPosition: ['0% 50%', '100% 50%', '0% 50%']
                  }}
                  transition={{ 
                    duration: 8, 
                    repeat: Infinity 
                  }}
                >
                  Transformation Complete
                </motion.h3>
                <p className="text-lg text-white/70 mt-3">From natural language to actionable database insights in seconds</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
                <motion.div 
                  className="bg-black/50 rounded-lg p-6 flex flex-col items-center justify-center border border-blue-500/20"
                  whileHover={{ 
                    y: -5,
                    boxShadow: '0 15px 30px -10px rgba(59, 130, 246, 0.2)'
                  }}
                >
                  <div className="text-5xl font-bold text-blue-400 mb-3">0.34s</div>
                  <div className="text-white/70 text-center text-lg">Average Query Time</div>
                </motion.div>
                <motion.div 
                  className="bg-black/50 rounded-lg p-6 flex flex-col items-center justify-center border border-purple-500/20"
                  whileHover={{ 
                    y: -5,
                    boxShadow: '0 15px 30px -10px rgba(139, 92, 246, 0.2)'
                  }}
                >
                  <div className="text-5xl font-bold text-purple-400 mb-3">98%</div>
                  <div className="text-white/70 text-center text-lg">Query Accuracy</div>
                </motion.div>
                <motion.div 
                  className="bg-black/50 rounded-lg p-6 flex flex-col items-center justify-center border border-pink-500/20"
                  whileHover={{ 
                    y: -5,
                    boxShadow: '0 15px 30px -10px rgba(236, 72, 153, 0.2)'
                  }}
                >
                  <div className="text-5xl font-bold text-pink-400 mb-3">5+</div>
                  <div className="text-white/70 text-center text-lg">Major SQL Dialects</div>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
} 