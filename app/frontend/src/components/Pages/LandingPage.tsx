import React from 'react';
import type { FC } from 'react';
import { Link } from 'react-router-dom';
import routes from '../../config/routes';
import ButtonShiny from '../ButtonShiny';
import AnimatedTextCycle from '../AnimatedTextCycle';
import { 
  ArrowForwardIcon,
  StorageIcon,
  CodeIcon,
  AutoAwesomeIcon,
  SpeedIcon,
  BoltIcon
} from '../ui/icons';

const LandingPage: FC = () => {
  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Hero section */}
      <div className="relative overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10 bg-[url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22 viewBox=%220 0 100 100%22%3E%3Cg fill-rule=%22evenodd%22%3E%3Cg fill=%22%236366f1%22 fill-opacity=%220.1%22%3E%3Cpath d=%22M0 0h10v10H0V0zm10 10h10v10H10V10zm10 0h10v10H20V10zm10 0h10v10H30V10zm40 0h10v10H70V10zm10 0h10v10H80V10zm10 0h10v10H90V10zm0-10h10v10H90V0zM0 20h10v10H0V20zm10 0h10v10H10V20zm10 0h10v10H20V20zm30 0h10v10H50V20zm10 0h10v10H60V20zm20 0h10v10H80V20zm10 0h10v10H90V20zM0 30h10v10H0V30zm30 0h10v10H30V30zm20 0h10v10H50V30zm10 0h10v10H60V30zm20 0h10v10H80V30zM0 40h10v10H0V40zm20 0h10v10H20V40zm10 0h10v10H30V40zm40 0h10v10H70V40zm20 0h10v10H90V40zM0 50h10v10H0V50zm10 0h10v10H10V50zm10 0h10v10H20V50zm20 0h10v10H40V50zm10 0h10v10H50V50zm10 0h10v10H60V50zm30 0h10v10H90V50zM0 60h10v10H0V60zm10 0h10v10H10V60zm20 0h10v10H30V60zm10 0h10v10H40V60zm10 0h10v10H50V60zm10 0h10v10H60V60zm20 0h10v10H80V60zM0 70h10v10H0V70zm20 0h10v10H20V70zm10 0h10v10H30V70zm10 0h10v10H40V70zm10 0h10v10H50V70zm30 0h10v10H80V70zM0 80h10v10H0V80zm10 0h10v10H10V80zm10 0h10v10H20V80zm30 0h10v10H50V80zm30 0h10v10H80V80zm10 0h10v10H90V80zM0 90h10v10H0V90zm30 0h10v10H30V90zm20 0h10v10H50V90zm30 0h10v10H80V90z%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')]"></div>
        
        {/* Hero content */}
        <div className="container mx-auto px-4 md:px-6 py-20 md:py-32 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-slate-100 to-indigo-400 bg-clip-text text-transparent">
              <span className="block">Democratizing SQL for</span>
              <AnimatedTextCycle
                words={[
                  "Business Leaders",
                  "Data Teams",
                  "Product Managers",
                  "Operations",
                  "Sales Teams",
                  "Marketing",
                  "Finance",
                  "Executives",
                  "Everyone"
                ]}
                interval={2000}
                reverse={true}
                variant="h1"
                component="span"
              />
            </h1>
            
            <p className="text-lg md:text-xl text-slate-300 mb-10 max-w-3xl mx-auto">
              Democratizing database access through the power of conversation.
              Ask in plain English, receive insights in seconds.
            </p>
            
            <div className="flex flex-wrap gap-4 justify-center">
              <Link to={routes.app} className="inline-block">
                <ButtonShiny label="TRY IT NOW ➜" />
              </Link>
              
              <a href="#features" className="inline-block">
                <ButtonShiny 
                  label="LEARN MORE ⚡" 
                  className="bg-transparent border border-indigo-500/50 hover:border-purple-500/80 hover:bg-indigo-500/10"
                />
              </a>
            </div>
          </div>
        </div>
      </div>
      
      {/* Features section */}
      <div id="features" className="py-16 md:py-24 bg-gradient-to-b from-slate-900/0 to-slate-900/80">
        <div className="container mx-auto px-4 md:px-6">
          <div className="text-center mb-12 md:mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-slate-100 to-indigo-400 bg-clip-text text-transparent">
              Intelligent Features
            </h2>
            <p className="text-lg text-slate-300 max-w-2xl mx-auto">
              Our advanced AI system transforms your natural language into powerful database queries
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
            {/* Feature cards */}
            <div className="bg-slate-800/75 backdrop-blur rounded-xl p-6 border border-indigo-500/30 shadow-lg shadow-indigo-500/10 hover:-translate-y-1 transition-transform duration-300">
              <div className="w-12 h-12 bg-indigo-500/20 rounded-lg flex items-center justify-center mb-4">
                <AutoAwesomeIcon className="text-indigo-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">AI-Powered Intent Analysis</h3>
              <p className="text-slate-300">Our advanced NLP engine understands business intent, identifies entities, and maps relationships in your natural language queries.</p>
            </div>
            
            <div className="bg-slate-800/75 backdrop-blur rounded-xl p-6 border border-emerald-500/30 shadow-lg shadow-emerald-500/10 hover:-translate-y-1 transition-transform duration-300">
              <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center mb-4">
                <StorageIcon className="text-emerald-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Multi-Database Support</h3>
              <p className="text-slate-300">Connect to PostgreSQL, MySQL, SQLite, Oracle, and SQL Server databases seamlessly.</p>
            </div>
            
            <div className="bg-slate-800/75 backdrop-blur rounded-xl p-6 border border-amber-500/30 shadow-lg shadow-amber-500/10 hover:-translate-y-1 transition-transform duration-300">
              <div className="w-12 h-12 bg-amber-500/20 rounded-lg flex items-center justify-center mb-4">
                <BoltIcon className="text-amber-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Query Optimization</h3>
              <p className="text-slate-300">Automatically optimize SQL for performance with efficient JOINs and indexing.</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* CTA section */}
      <div className="py-16 md:py-24 relative overflow-hidden">
        <div className="absolute inset-0 opacity-20 bg-gradient-to-b from-indigo-900/20 to-purple-900/20"></div>
        
        <div className="container mx-auto px-4 md:px-6 relative z-10">
          <div className="bg-slate-800/80 backdrop-blur-sm border border-indigo-500/30 rounded-2xl p-8 md:p-12 max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-slate-100 to-indigo-400 bg-clip-text text-transparent">
              Join the Future of Database Interaction
            </h2>
            <p className="text-lg text-slate-300 mb-8 max-w-2xl mx-auto">
              Transform how your organization interacts with data. Empower every team member 
              to access insights without SQL expertise or technical bottlenecks.
            </p>
            <Link to={routes.app} className="inline-block">
              <ButtonShiny 
                label="Start Your Data Journey" 
                endIcon={<ArrowForwardIcon />}
                className="px-8 py-3 text-lg"
              />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage; 