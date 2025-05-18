import { useState, useEffect } from 'react';
import { SQLChatbot } from './SQLChatbot';
import { DatabaseConnectionsPage } from './DatabaseConnectionsPage';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { Database, History, Settings, RefreshCw, Home, Info, MessageSquare, Menu, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { useDatabaseConnection, useMediaQuery } from '@/lib/hooks';
import { SettingsPage } from './SettingsPage';
import { HistoryPage } from './HistoryPage';

interface SidebarItemProps {
  icon: React.ReactNode;
  label: string;
  active: boolean;
  onClick: () => void;
}

function SidebarItem({ icon, label, active, onClick }: SidebarItemProps) {
  return (
    <motion.button
      onClick={onClick}
      className={cn(
        "flex items-center gap-3 px-4 py-3 w-full text-left rounded-lg transition-all",
        active 
          ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/20" 
          : "text-gray-400 hover:bg-white/[0.06] hover:text-gray-200 border border-transparent"
      )}
      whileHover={{ x: active ? 0 : 4 }}
      whileTap={{ scale: 0.98 }}
    >
      <div className="shrink-0">
        {icon}
      </div>
      <span className="font-medium">{label}</span>
      {active && (
        <motion.div 
          className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-400"
          layoutId="activeIndicator"
        />
      )}
    </motion.button>
  );
}

export function DashboardPage() {
  const [currentPage, setCurrentPage] = useState<'chat' | 'history' | 'connections' | 'settings'>('chat');
  const { connectionInfo, loading, error, checkConnection, connect } = useDatabaseConnection();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isDesktop = useMediaQuery('(min-width: 768px)');
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Check URL parameters on component mount
  useEffect(() => {
    const tabParam = searchParams.get('tab');
    
    // Set the current page based on URL parameter if it exists and is valid
    if (tabParam) {
      if (tabParam === 'connections' || tabParam === 'history' || tabParam === 'settings' || tabParam === 'chat') {
        setCurrentPage(tabParam as 'chat' | 'history' | 'connections' | 'settings');
      }
    }
  }, [searchParams]);
  
  // Auto-connect to sample database on mount if not already connected
  useEffect(() => {
    const autoConnectToSampleDatabase = async () => {
      if (!connectionInfo.connected) {
        try {
          await connect({
            db_type: 'sqlite',
            db_name: 'sample_huge.db'
          });
        } catch (error) {
          console.error('Error auto-connecting to sample database:', error);
        }
      }
    };

    // Add a small delay to let the connection status check complete first
    const timer = setTimeout(() => {
      autoConnectToSampleDatabase();
    }, 1000);
    
    return () => clearTimeout(timer);
  }, [connectionInfo.connected, connect]);
  
  const handleNavItemClick = (page: 'chat' | 'history' | 'connections' | 'settings') => {
    setCurrentPage(page);
    
    // Update URL with the new tab
    setSearchParams({ tab: page });
    
    // Close sidebar on mobile after navigation
    if (!isDesktop) {
      setSidebarOpen(false);
    }
  };

  return (
    <div className="flex h-screen max-h-screen overflow-hidden bg-black text-white">
      {/* Background elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse delay-700" />
      </div>
      
      {/* Mobile header with menu button */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-16 border-b border-white/[0.08] bg-black/90 backdrop-blur-md z-50 flex items-center justify-between px-4">
        <h1 className="font-heading text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-400" />
          Text-to-SQL
        </h1>
<button
  aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
  onClick={() => setSidebarOpen(!sidebarOpen)}
  className="p-2 rounded-lg bg-white/[0.05] text-gray-300 hover:bg-white/[0.1] transition-colors"
>
          {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>
      
      {/* Sidebar - desktop permanent, mobile toggleable */}
      <AnimatePresence>
        {(isDesktop || sidebarOpen) && (
          <motion.div 
            className={cn(
              "w-64 border-r border-white/[0.08] bg-black/95 backdrop-blur-md flex flex-col relative z-40",
              isDesktop ? "relative" : "fixed inset-y-0 left-0"  // Fixed position on mobile, relative on desktop
            )}
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -100, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            {/* Only show header in desktop view or when sidebar is open on mobile */}
            <div className="p-5 border-b border-white/[0.08] md:block hidden">
              <motion.h1 
                className="font-heading text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent flex items-center gap-2"
                initial={{ y: -10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.1, duration: 0.3 }}
              >
                <Database className="w-5 h-5 text-indigo-400" />
                Text-to-SQL
              </motion.h1>
              <motion.p 
                className="text-sm text-gray-400"
                initial={{ y: -10, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.3 }}
              >
                Natural language to SQL queries
              </motion.p>
            </div>
            
            {/* Add padding top on mobile to account for the fixed header */}
            <div className={cn("p-3 space-y-1 flex-1 overflow-auto", isDesktop ? "pt-3" : "pt-20")}>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3, duration: 0.3 }}>
                <SidebarItem 
                  icon={<MessageSquare className="w-5 h-5" />} 
                  label="Chat" 
                  active={currentPage === 'chat'} 
                  onClick={() => handleNavItemClick('chat')}
                />
              </motion.div>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4, duration: 0.3 }}>
                <SidebarItem 
                  icon={<History className="w-5 h-5" />} 
                  label="History" 
                  active={currentPage === 'history'} 
                  onClick={() => handleNavItemClick('history')}
                />
              </motion.div>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5, duration: 0.3 }}>
                <SidebarItem 
                  icon={<Database className="w-5 h-5" />} 
                  label="Connections" 
                  active={currentPage === 'connections'} 
                  onClick={() => handleNavItemClick('connections')}
                />
              </motion.div>
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6, duration: 0.3 }}>
                <SidebarItem 
                  icon={<Settings className="w-5 h-5" />} 
                  label="Settings" 
                  active={currentPage === 'settings'} 
                  onClick={() => handleNavItemClick('settings')}
                />
              </motion.div>
            </div>
            
            {/* Navigation links to other parts of the app */}
            <div className="p-3 border-t border-white/[0.08]">
              <div className="px-4 py-2">
                <div className="text-xs text-gray-500 uppercase tracking-wider font-medium">Navigation</div>
              </div>
              <div className="space-y-1"> 
                <Link to="/" className="block mb-1">
                  <SidebarItem 
                    icon={<Home className="w-5 h-5" />} 
                    label="Home" 
                    active={false} 
                    onClick={() => {}}
                  />
                </Link>
                <Link to="/about">
                  <SidebarItem 
                    icon={<Info className="w-5 h-5" />} 
                    label="About" 
                    active={false} 
                    onClick={() => {}}
                  />
                </Link>
              </div>
            </div>
            
            <motion.div 
              className="p-4 border-t border-white/[0.08] bg-white/[0.02]"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.7, duration: 0.3 }}
            >
              <div className="flex items-center justify-between">
                <div className="text-xs text-gray-500 uppercase tracking-wider font-medium">Database</div>
                <motion.button 
                  onClick={() => checkConnection()} 
                  className="text-gray-400 hover:text-gray-300 transition-colors"
                  disabled={loading}
                  whileHover={{ rotate: 180 }}
                  transition={{ duration: 0.3 }}
                >
                  <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} />
                </motion.button>
              </div>
              
              <div className="mt-2 p-2 rounded-md bg-white/[0.03] border border-white/[0.05]">
                {connectionInfo.connected ? (
                  <div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 rounded-full bg-green-500 mr-2" />
                      <span className="text-xs font-medium text-green-400">Connected</span>
                    </div>
                    <div className="mt-1 text-xs text-gray-400 truncate">
                      {connectionInfo.dbType === 'sqlite' ? 'SQLite' : connectionInfo.dbType}
                      {connectionInfo.dbName && `: ${connectionInfo.dbName}`}
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center">
                      <div className="w-2 h-2 rounded-full bg-red-500 mr-2" />
                      <span className="text-xs font-medium text-red-400">Disconnected</span>
                    </div>
                    <div className="mt-1 text-xs text-gray-400">
                      Configure in Connections tab
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Overlay to close sidebar on mobile */}
      {!isDesktop && sidebarOpen && (
        <motion.div
          className="fixed inset-0 bg-black/60 z-30 md:hidden"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Main content area with padding adjustments for mobile */}
      <div className="flex-1 overflow-hidden pt-16 md:pt-0">
        <AnimatePresence mode="wait">
          {currentPage === 'chat' && (
            <motion.div
              key="chat"
              className="h-full"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <SQLChatbot />
            </motion.div>
          )}
          
          {currentPage === 'history' && (
            <motion.div
              key="history"
              className="h-full"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <HistoryPage />
            </motion.div>
          )}
          
          {currentPage === 'connections' && (
            <motion.div
              key="connections"
              className="h-full"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <DatabaseConnectionsPage />
            </motion.div>
          )}
          
          {currentPage === 'settings' && (
            <motion.div
              key="settings"
              className="h-full"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <SettingsPage />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
} 