import { motion } from "framer-motion";
import { cn } from "../../lib/utils";
import BackgroundRippleEffect from "./background-ripple-effect";

// Import icons - we'll use literals for simplicity here
// You can replace these with actual icon imports from your preferred icon library
const icons = {
  AIInsights: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 3L19 8.5V15.5L12 21L5 15.5V8.5L12 3Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 12L12 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <circle cx="12" cy="8" r="1" fill="currentColor"/>
    </svg>
  ),
  Security: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2L4 5V11.09C4 16.14 7.41 20.85 12 22C16.59 20.85 20 16.14 20 11.09V5L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M9 12L11 14L15 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  FastAPI: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M13 10H17.5C19.985 10 22 7.985 22 5.5C22 3.015 19.985 1 17.5 1H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M13 14H17.5C19.985 14 22 16.015 22 18.5C22 20.985 19.985 23 17.5 23H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M2 5H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M2 9H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M2 14H7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M2 18H5" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M11 2V22" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  ),
  Automation: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect x="2" y="2" width="20" height="20" rx="4" stroke="currentColor" strokeWidth="2"/>
      <rect x="6" y="6" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="2"/>
      <rect x="14" y="6" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="2"/>
      <rect x="6" y="14" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="2"/>
      <rect x="14" y="14" width="4" height="4" rx="1" stroke="currentColor" strokeWidth="2"/>
    </svg>
  ),
  UiUx: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M16 8.99976V20.9998H2V8.99976H16Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M22 2.99976H8V14.9998H22V2.99976Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 18H6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  ),
  Performance: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M18 20V10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 20V4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M6 20V14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
};

const features = [
  {
    title: "AI-Powered Insights",
    description: "Ask questions in plain English and get accurate SQL queries. Our system understands natural language and converts it precisely to the database operations you need.",
    icon: icons.AIInsights,
    accent: "from-blue-500/20 to-indigo-700/20",
    borderAccent: "border-blue-500/20",
    bgAccent: "bg-gradient-to-br from-blue-500/10 to-indigo-700/10",
    delay: 0.1
  },
  {
    title: "Multi-Database Support",
    description: "Works with PostgreSQL, MySQL, MSSQL, Oracle, and SQLite. Connect to any supported database and start querying immediately.",
    icon: icons.Security,
    accent: "from-cyan-500/20 to-teal-700/20",
    borderAccent: "border-cyan-500/20",
    bgAccent: "bg-gradient-to-br from-cyan-500/10 to-teal-700/10",
    delay: 0.2
  },
  {
    title: "Real-time Query Generation",
    description: "Generate optimized SQL in seconds with context-aware agents that understand your database schema and query intentions.",
    icon: icons.FastAPI,
    accent: "from-purple-500/20 to-pink-700/20",
    borderAccent: "border-purple-500/20",
    bgAccent: "bg-gradient-to-br from-purple-500/10 to-pink-700/10",
    delay: 0.3
  },
  {
    title: "Intelligent Schema Mapping",
    description: "Our system automatically maps your natural language entities to the correct database tables and columns, even handling ambiguous references.",
    icon: icons.Automation,
    accent: "from-amber-500/20 to-orange-700/20",
    borderAccent: "border-amber-500/20",
    bgAccent: "bg-gradient-to-br from-amber-500/10 to-orange-700/10",
    delay: 0.4
  },
  {
    title: "Educational Explanations",
    description: "Learn SQL as you go with detailed explanations of every generated query, helping you understand the structure and function of database operations.",
    icon: icons.UiUx,
    accent: "from-green-500/20 to-emerald-700/20", 
    borderAccent: "border-green-500/20",
    bgAccent: "bg-gradient-to-br from-green-500/10 to-emerald-700/10",
    delay: 0.5
  },
  {
    title: "Enterprise-Grade Security",
    description: "All queries are validated and sanitized, with built-in protection against SQL injection and performance safeguards.",
    icon: icons.Performance,
    accent: "from-rose-500/20 to-red-700/20",
    borderAccent: "border-rose-500/20",
    bgAccent: "bg-gradient-to-br from-rose-500/10 to-red-700/10",
    delay: 0.6
  }
];

export default function FeaturesBento() {
  return (
    <section className="relative py-8 md:py-16 pb-4 md:pb-8 px-4 sm:px-6 md:px-8 lg:px-12 overflow-hidden">
      {/* Add Background Effect */}
      <div className="absolute inset-0 z-0">
        <BackgroundRippleEffect className="opacity-100" />
      </div>
      
      {/* Decorative elements */}
      <div className="absolute inset-0 pointer-events-none z-10">
        <div className="absolute -top-40 right-[10%] w-48 md:w-72 h-48 md:h-72 bg-indigo-500/10 rounded-full filter blur-3xl" />
        <div className="absolute bottom-20 left-[5%] w-48 md:w-72 h-48 md:h-72 bg-blue-500/10 rounded-full filter blur-3xl" />
      </div>
      
      <div className="container mx-auto max-w-7xl relative z-20">
        <motion.div 
          className="text-center mb-8 md:mb-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-heading text-3xl md:text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-600 bg-clip-text text-transparent">
            Transform Data Access
          </h2>
          <p className="mt-3 md:mt-4 text-base md:text-lg text-white/70 max-w-2xl mx-auto">
            Ask questions in plain English and instantly get the SQL you need.
            No database expertise required.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-8">
          {features.map((feature) => (
            <motion.div
              key={feature.title}
              className={cn(
                "group relative p-4 sm:p-6 md:p-8 rounded-xl md:rounded-2xl border backdrop-blur-sm overflow-hidden shadow-lg",
                "hover:border-white/20 transition-all duration-300",
                feature.borderAccent,
                feature.bgAccent
              )}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: feature.delay }}
              whileHover={{ 
                y: -8, 
                transition: { duration: 0.2 } 
              }}
            >
              {/* Feature content */}
              <div className="relative z-10">
                <div className="flex flex-col items-start gap-3 md:gap-4 mb-3 md:mb-5">
                  <div className={cn(
                    "flex-shrink-0 rounded-lg md:rounded-xl p-2 md:p-3",
                    "bg-white/10 text-white"
                  )}>
                    <feature.icon />
                  </div>
                  <h3 className="font-heading text-xl md:text-2xl font-semibold text-white">
                    {feature.title}
                  </h3>
                </div>
                <p className="text-white/70 leading-relaxed text-sm md:text-base">
                  {feature.description}
                </p>
              </div>
              
              {/* Decorative gradient */}
              <div className={cn(
                "absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100",
                "bg-gradient-to-br",
                feature.accent
              )} />
              
              {/* Decorative elements */}
              <div className="absolute -right-4 -bottom-4 w-24 md:w-32 h-24 md:h-32 bg-white/5 rounded-full filter blur-xl opacity-0 group-hover:opacity-70 transition-opacity duration-300" />
              
              {/* Shine effect on hover */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.05] to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
} 