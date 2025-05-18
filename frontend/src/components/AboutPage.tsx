import { motion } from 'framer-motion';
import { Info, Database, Code, Brain, Github, Twitter, Mail, ExternalLink } from 'lucide-react';

export function AboutPage() {
  // Define variables outside of JSX
  const supportEmail = 'akshaysisodia.studies' + '@' + 'gmail.com';
  // Hardcoded Twitter username
  const twitterUsername = 'akshay__sisodia';

  return (
    <div className="flex-1 p-6 overflow-auto bg-black/30 backdrop-blur-sm">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent mb-2">
            About Agentic Text2SQL
          </h1>
          <p className="text-gray-400">
            Transform natural language to SQL with advanced AI agents
          </p>
          <p className="text-gray-300 mt-2">
            Created by Akshay Sisodia
          </p>
        </header>

        <div className="grid grid-cols-1 gap-8">
          {/* Project Overview */}
          <motion.section 
            className="bg-white/[0.03] border border-white/10 rounded-lg p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
              <Info className="w-5 h-5 text-indigo-400" />
              Project Overview
            </h2>
            
            <div className="space-y-4 text-gray-300">
              <p>
                Agentic Text2SQL is an AI-powered tool that translates natural language questions into SQL queries. It allows users to interact with databases using plain English, making data access and analysis more intuitive and accessible to everyone.
              </p>
              <p>
                Built with a focus on accuracy and explainability, the system uses advanced machine learning models to understand your intent and generate optimized SQL queries that match your database schema.
              </p>
              <p className="italic text-gray-400">
                "Democratizing data access by bridging the gap between natural language and database queries."
              </p>
            </div>
          </motion.section>
          
          {/* Key Features */}
          <motion.section 
            className="bg-white/[0.03] border border-white/10 rounded-lg p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-400" />
              Key Features
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-lg">
                <h3 className="text-indigo-300 font-medium mb-2 flex items-center gap-2">
                  <Brain className="w-4 h-4" />
                  Intelligent Query Understanding
                </h3>
                <p className="text-gray-400 text-sm">
                  Our system understands the intent behind your questions, identifies relevant entities, and resolves ambiguities to generate accurate SQL.
                </p>
              </div>
              
              <div className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-lg">
                <h3 className="text-indigo-300 font-medium mb-2 flex items-center gap-2">
                  <Code className="w-4 h-4" />
                  Optimized SQL Generation
                </h3>
                <p className="text-gray-400 text-sm">
                  Produces efficient SQL that follows best practices with proper joins, conditions, and database-specific syntax.
                </p>
              </div>
              
              <div className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-lg">
                <h3 className="text-indigo-300 font-medium mb-2 flex items-center gap-2">
                  <Database className="w-4 h-4" />
                  Multiple Database Support
                </h3>
                <p className="text-gray-400 text-sm">
                  Connect to PostgreSQL, MySQL, SQLite, Oracle, and SQL Server databases with a simple configuration.
                </p>
              </div>
              
              <div className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-lg">
                <h3 className="text-indigo-300 font-medium mb-2 flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  Educational Explanations
                </h3>
                <p className="text-gray-400 text-sm">
                  Get detailed explanations of generated SQL, helping you learn and understand database concepts.
                </p>
              </div>
            </div>
          </motion.section>
          
          {/* Technology Stack */}
          <motion.section 
            className="bg-white/[0.03] border border-white/10 rounded-lg p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
              <Code className="w-5 h-5 text-indigo-400" />
              Technology Stack
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-indigo-300 font-medium mb-2">Backend</h3>
                <ul className="space-y-2 text-gray-400">
                  <li className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span>Python with FastAPI framework</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span>PydanticAI for agent orchestration</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span>SQLAlchemy for database interactions</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span>State-of-the-art language models</span>
                  </li>
                </ul>
              </div>
              
              <div>
                <h3 className="text-indigo-300 font-medium mb-2">Frontend</h3>
                <ul className="space-y-2 text-gray-400">
                  <li className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span>React with TypeScript</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span>TailwindCSS for styling</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span>Framer Motion for animations</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    <span>Modern, responsive UI design</span>
                  </li>
                </ul>
              </div>
            </div>
          </motion.section>
          
          {/* Contact Information */}
          <motion.section 
            className="bg-white/[0.03] border border-white/10 rounded-lg p-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
              <Mail className="w-5 h-5 text-indigo-400" />
              Contact & Resources
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <a 
                href="https://github.com/akshay-sisodia/agentic-text2sql" 
                target="_blank"
                rel="noopener noreferrer"
                className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-lg flex items-center gap-3 hover:bg-white/[0.05] transition-colors"
              >
                <Github className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-white font-medium">GitHub Repository</p>
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <span>akshay-sisodia</span>
                    <ExternalLink className="w-3 h-3" />
                  </p>
                </div>
              </a>
              
              {/* Twitter link (always visible now with default fallback) */}
              <a 
                href={`https://twitter.com/${twitterUsername}`}
                target="_blank"
                rel="noopener noreferrer"
                className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-lg flex items-center gap-3 hover:bg-white/[0.05] transition-colors"
              >
                <Twitter className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-white font-medium">Twitter</p>
                  <p className="text-xs text-gray-500 flex items-center gap-1">
                    <span>@{twitterUsername}</span>
                    <ExternalLink className="w-3 h-3" />
                  </p>
                </div>
              </a>

              <a 
                href={`mailto:${supportEmail}`}
                className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-lg flex items-center gap-3 hover:bg-white/[0.05] transition-colors"
              >
                <Mail className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-white font-medium">Email Support</p>
                  <p className="text-xs text-gray-500">{supportEmail}</p>
                </div>
              </a>
            </div>
          </motion.section>
        </div>
      </div>
    </div>
  );
} 