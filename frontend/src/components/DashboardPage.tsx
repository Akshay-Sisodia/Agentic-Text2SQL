import { useState, useEffect } from 'react';
import { SQLChatbot } from './SQLChatbot';
import { DatabaseConnectionsPage } from './DatabaseConnectionsPage';
import { Link } from 'react-router-dom';
import { Database, History, Settings, RefreshCw, Home, Info, MessageSquare } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { useDatabaseConnection } from '@/lib/hooks';
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
  
  // Check URL parameters on component mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab');
    
    // Set the current page based on URL parameter if it exists and is valid
    if (tabParam) {
      if (tabParam === 'connections' || tabParam === 'history' || tabParam === 'settings' || tabParam === 'chat') {
        setCurrentPage(tabParam as 'chat' | 'history' | 'connections' | 'settings');
      }
    }
  }, []);
  
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
  
  // Function to handle showing empty state messages for each tab
  // Removed unused renderChatEmpty function

  return (
    <div className="flex h-screen max-h-screen overflow-hidden bg-black text-white">
      {/* Background elements */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full mix-blend-normal filter blur-[128px] animate-pulse delay-700" />
      </div>
      
      {/* Sidebar */}
      <motion.div 
        className="w-64 border-r border-white/[0.08] bg-black/60 backdrop-blur-md flex flex-col relative z-10"
        initial={{ x: -20, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="p-5 border-b border-white/[0.08]">
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
        
        <div className="p-3 space-y-1 flex-1 overflow-auto">
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3, duration: 0.3 }}>
            <SidebarItem 
              icon={<MessageSquare className="w-5 h-5" />} 
              label="Chat" 
              active={currentPage === 'chat'} 
              onClick={() => setCurrentPage('chat')}
            />
          </motion.div>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4, duration: 0.3 }}>
            <SidebarItem 
              icon={<History className="w-5 h-5" />} 
              label="History" 
              active={currentPage === 'history'} 
              onClick={() => setCurrentPage('history')}
            />
          </motion.div>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5, duration: 0.3 }}>
            <SidebarItem 
              icon={<Database className="w-5 h-5" />} 
              label="Connections" 
              active={currentPage === 'connections'} 
              onClick={() => setCurrentPage('connections')}
            />
          </motion.div>
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6, duration: 0.3 }}>
            <SidebarItem 
              icon={<Settings className="w-5 h-5" />} 
              label="Settings" 
              active={currentPage === 'settings'} 
              onClick={() => setCurrentPage('settings')}
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
          <div className="flex items-center gap-2 mt-2">
            <motion.div 
              className={cn(
                "w-2 h-2 rounded-full", 
                connectionInfo.connected ? "bg-green-500" : "bg-red-500"
              )}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ 
                type: "spring", 
                stiffness: 500, 
                damping: 15, 
                delay: 0.8 
              }}
            />
            <span className="text-sm font-medium text-gray-300">
              {connectionInfo.connected ? (connectionInfo.dbName || 'Connected') : 'Disconnected'}
            </span>
          </div>
          {error && (
            <div className="mt-1 text-xs text-red-400 truncate">{error}</div>
          )}
          {!connectionInfo.connected && !error && (
            <div className="mt-1 text-xs text-gray-500 truncate">{connectionInfo.message}</div>
          )}
        </motion.div>
      </motion.div>
      
      {/* Main Content */}
      <div className="flex-1 overflow-hidden relative z-10">
        <AnimatePresence mode="wait">
          {currentPage === 'chat' && (
            <motion.div 
              key="chat"
              className="h-full"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
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
              transition={{ duration: 0.3 }}
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
              transition={{ duration: 0.3 }}
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
              transition={{ duration: 0.3 }}
            >
              <SettingsPage />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
} 