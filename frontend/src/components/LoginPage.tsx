import { useState } from 'react';
import { motion } from 'framer-motion';
import { Lock, User, ArrowRight, Github } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';

export function LoginPage() {
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
    rememberMe: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // In a real app, you would actually check credentials with an API
      // For now, we'll simulate a login
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulate credentials check
      if (credentials.username === 'demo' && credentials.password === 'password') {
        // Set login state (would use actual auth logic in a real app)
        localStorage.setItem('isAuthenticated', 'true');
        localStorage.setItem('user', JSON.stringify({ username: credentials.username }));
        
        // Redirect to dashboard
        navigate('/dashboard');
      } else {
        setError('Invalid username or password');
      }
    } catch (error) {
      setError('An error occurred during login');
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center p-6">
      {/* Background elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse delay-700" />
      </div>
      
      <div className="relative z-10 w-full max-w-md">
        <motion.div 
          className="bg-white/[0.03] backdrop-blur-md border border-white/[0.05] rounded-lg p-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent">
              Login to Text2SQL
            </h1>
            <p className="text-gray-400 mt-2">
              Sign in to access your dashboard
            </p>
          </div>
          
          {error && (
            <div className="mb-6 p-3 bg-red-900/20 border border-red-500/20 rounded-md text-red-300 text-sm">
              {error}
            </div>
          )}
          
          <form onSubmit={handleSubmit}>
            <div className="space-y-6">
              <div>
                <label className="block text-sm text-gray-400 mb-1" htmlFor="username">
                  Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-gray-500" />
                  </div>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    value={credentials.username}
                    onChange={handleChange}
                    required
                    className="block w-full pl-10 pr-3 py-2.5 bg-white/[0.03] border border-white/10 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Enter your username"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm text-gray-400 mb-1" htmlFor="password">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-500" />
                  </div>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    value={credentials.password}
                    onChange={handleChange}
                    required
                    className="block w-full pl-10 pr-3 py-2.5 bg-white/[0.03] border border-white/10 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Enter your password"
                  />
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="rememberMe"
                    type="checkbox"
                    checked={credentials.rememberMe}
                    onChange={handleChange}
                    className="h-4 w-4 bg-white/[0.03] border border-white/10 rounded text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-400">
                    Remember me
                  </label>
                </div>
                
                <div className="text-sm">
                  <a href="#" className="text-indigo-400 hover:text-indigo-300">
                    Forgot password?
                  </a>
                </div>
              </div>
              
              <div>
                <button
                  type="submit"
                  disabled={loading}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-md text-white transition-colors",
                    "bg-indigo-600 hover:bg-indigo-700",
                    loading && "opacity-70 cursor-not-allowed"
                  )}
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white/90 rounded-full animate-spin"></div>
                      <span>Signing in...</span>
                    </>
                  ) : (
                    <>
                      <span>Sign In</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </form>
          
          <div className="mt-8 pt-6 border-t border-white/[0.05]">
            <div className="text-center">
              <p className="text-sm text-gray-400 mb-4">
                Don't have an account?{' '}
                <Link to="/register" className="text-indigo-400 hover:text-indigo-300">
                  Sign up
                </Link>
              </p>
              
              <p className="text-xs text-gray-500 mb-4">
                Demo credentials: username "demo" / password "password"
              </p>
              
              <div className="flex justify-center">
                <button 
                  type="button"
                  className="flex items-center gap-2 px-4 py-2 bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 rounded-md text-gray-300 transition-colors"
                >
                  <Github className="w-4 h-4" />
                  <span>Continue with GitHub</span>
                </button>
              </div>
            </div>
          </div>
        </motion.div>
        
        {/* Return link */}
        <div className="text-center mt-6">
          <Link to="/" className="text-sm text-gray-400 hover:text-gray-300">
            Return to homepage
          </Link>
        </div>
      </div>
    </div>
  );
} 