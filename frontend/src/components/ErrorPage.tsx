import { motion } from 'framer-motion';
import { AlertTriangle, Home, ArrowLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

interface ErrorPageProps {
  statusCode?: number;
  title?: string;
  message?: string;
}

export function ErrorPage({ 
  statusCode = 404, 
  title = "Page Not Found", 
  message = "The page you're looking for doesn't exist or has been moved."
}: ErrorPageProps) {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6">
      {/* Background elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-red-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse delay-700" />
      </div>
      
      <motion.div 
        className="relative z-10 max-w-md w-full bg-white/[0.03] backdrop-blur-md border border-white/[0.05] rounded-lg p-8 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="flex justify-center mb-6">
          <div className="w-24 h-24 bg-red-500/10 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-12 h-12 text-red-400" />
          </div>
        </div>
        
        <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-red-400 to-purple-500 bg-clip-text text-transparent">
          {statusCode}
        </h1>
        
        <h2 className="text-2xl font-semibold mb-4 text-white">
          {title}
        </h2>
        
        <p className="text-gray-400 mb-8">
          {message}
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/"
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            <Home className="w-4 h-4" />
            <span>Go Home</span>
          </Link>
          
          <button
            title="Return to previous page"
           onClick={() => navigate(-1)}
           className="px-6 py-2.5 bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Go Back</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
} 