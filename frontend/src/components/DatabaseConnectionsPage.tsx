import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import type { DatabaseConnectionRequest } from '@/lib/api';
import { useDatabaseConnection } from '@/lib/hooks';
import { Database, Server, User, Key, RefreshCw, CheckCircle, XCircle, BookOpen } from 'lucide-react';

export function DatabaseConnectionsPage() {
  const { connectionInfo, loading, error, connect, checkConnection } = useDatabaseConnection();
  const [formData, setFormData] = useState<DatabaseConnectionRequest>({
    db_type: 'postgresql',
    db_name: '',
    db_user: '',
    db_password: '',
    db_host: 'localhost',
    db_port: 5432
  });
  const [connecting, setConnecting] = useState(false);
  const [connectionResult, setConnectionResult] = useState<{ success: boolean; message: string } | null>(null);
  const [useConnectionString, setUseConnectionString] = useState(false);

  // Add custom scrollbar styles using useEffect
  useEffect(() => {
    // Create a style element
    const styleElement = document.createElement('style');
    
    // Add scrollbar styles
    styleElement.textContent = `
      .db-connections-container::-webkit-scrollbar {
        width: 8px;
        height: 8px;
      }
      
      .db-connections-container::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
      }
      
      .db-connections-container::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 4px;
      }
      
      .db-connections-container::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.15);
      }
    `;
    
    // Append style to head
    document.head.appendChild(styleElement);
    
    // Cleanup on unmount
    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    // If changing to a connection string, enable that mode
    if (name === 'database_url' && value && !useConnectionString) {
      setUseConnectionString(true);
    }
    
    setFormData(prev => ({
      ...prev,
      [name]: name === 'db_port' ? parseInt(value, 10) || '' : value
    }));
  };

  const connectToSampleDatabase = async () => {
    setConnecting(true);
    setConnectionResult(null);
    
    try {
      // Connect to sample SQLite database
      const result = await connect({
        db_type: 'sqlite',
        db_name: 'sample_huge.db'
      });
      setConnectionResult(result);
    } catch (error) {
      setConnectionResult({
        success: false,
        message: 'Failed to connect to sample database'
      });
    } finally {
      setConnecting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnecting(true);
    setConnectionResult(null);
    
    try {
      // If using connection string, only send that
      const connectionData = useConnectionString 
        ? { database_url: formData.database_url }
        : {
            db_type: formData.db_type,
            db_name: formData.db_name,
            db_user: formData.db_user,
            db_password: formData.db_password,
            db_host: formData.db_host,
            db_port: formData.db_port
          };
          
      const result = await connect(connectionData);
      setConnectionResult(result);
    } catch (error) {
      setConnectionResult({
        success: false,
        message: 'Failed to connect to database'
      });
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-64px)] bg-black/30 backdrop-blur-sm">
      <div className="flex-1 p-6 overflow-y-auto relative db-connections-container">
        <div className="max-w-3xl mx-auto pb-12">
          <header className="mb-8">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent mb-2">
              Database Connections
            </h1>
            <p className="text-gray-400">
              Connect to your database to start querying with natural language.
            </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Connection Status Card */}
            <div className="bg-white/[0.03] border border-white/10 rounded-lg p-6 h-fit">
              <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                <Database className="w-5 h-5 text-indigo-400" />
                Current Connection
              </h2>
              
              <div className="flex items-center gap-2 mb-4">
                <div className={cn(
                  "w-3 h-3 rounded-full", 
                  connectionInfo.connected ? "bg-green-500" : "bg-red-500"
                )}></div>
                <span className="text-gray-300 font-medium">
                  {connectionInfo.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              {connectionInfo.connected && (
                <div className="space-y-4">
                  {connectionInfo.dbName && (
                    <div>
                      <div className="text-sm text-gray-400 mb-1">Database</div>
                      <div className="bg-white/[0.03] border border-white/10 rounded px-3 py-2 text-white">
                        {connectionInfo.dbName}
                      </div>
                    </div>
                  )}
                  
                  {connectionInfo.dbType && (
                    <div>
                      <div className="text-sm text-gray-400 mb-1">Type</div>
                      <div className="bg-white/[0.03] border border-white/10 rounded px-3 py-2 text-white">
                        {connectionInfo.dbType}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {error && (
                <div className="text-sm text-red-400 mb-4">{error}</div>
              )}
              
              <button
                onClick={() => checkConnection()} 
                disabled={loading}
                className={cn(
                  "w-full flex items-center justify-center gap-2 py-2 px-4 rounded-md mt-4",
                  "bg-indigo-600/20 text-indigo-300 border border-indigo-600/30",
                  "hover:bg-indigo-600/30 transition-colors",
                  loading && "opacity-70 cursor-not-allowed"
                )}
              >
                <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
                <span>{loading ? 'Checking...' : 'Refresh Status'}</span>
              </button>
            </div>

            {/* Connection Form */}
            <div className="lg:col-span-2 bg-white/[0.03] border border-white/10 rounded-lg p-6">
              <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                <Server className="w-5 h-5 text-indigo-400" />
                Connect to Database
              </h2>
              
              {/* Sample Database Button */}
              <div className="mb-6">
                <button
                  type="button"
                  onClick={connectToSampleDatabase}
                  disabled={connecting}
                  className={cn(
                    "w-full flex items-center justify-center gap-2 py-3 px-4 rounded-md",
                    "bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium",
                    "hover:from-purple-700 hover:to-indigo-700 transition-colors",
                    "border border-indigo-500/50 shadow-lg",
                    connecting && "opacity-70 cursor-not-allowed"
                  )}
                >
                  <BookOpen className="w-5 h-5" />
                  <span>{connecting ? 'Connecting...' : 'Connect to Sample Database'}</span>
                </button>
                <p className="mt-2 text-xs text-center text-gray-400">
                  Use the pre-configured sample SQLite database for testing
                </p>
              </div>
              
              <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/10"></div>
                </div>
                <div className="relative flex justify-center text-xs">
                  <span className="px-2 bg-black/30 text-gray-400">Or connect to your own database</span>
                </div>
              </div>
              
              {connectionResult && (
                <div className={cn(
                  "mb-4 p-3 rounded-md flex items-center gap-2",
                  connectionResult.success 
                    ? "bg-green-900/20 border border-green-900/30 text-green-300" 
                    : "bg-red-900/20 border border-red-900/30 text-red-300"
                )}>
                  {connectionResult.success ? (
                    <CheckCircle className="w-5 h-5 flex-shrink-0" />
                  ) : (
                    <XCircle className="w-5 h-5 flex-shrink-0" />
                  )}
                  <span>{connectionResult.message}</span>
                </div>
              )}
              
              <form onSubmit={handleSubmit}>
                {/* Connection method toggle */}
                <div className="mb-6">
                  <div className="inline-flex items-center bg-white/[0.02] rounded-md p-0.5 border border-white/10">
                    <button
                      type="button"
                      className={cn(
                        "px-4 py-2 text-sm rounded",
                        !useConnectionString 
                          ? "bg-indigo-600 text-white" 
                          : "text-gray-400 hover:text-gray-300"
                      )}
                      onClick={() => setUseConnectionString(false)}
                    >
                      Connection Details
                    </button>
                    <button
                      type="button"
                      className={cn(
                        "px-4 py-2 text-sm rounded",
                        useConnectionString 
                          ? "bg-indigo-600 text-white" 
                          : "text-gray-400 hover:text-gray-300"
                      )}
                      onClick={() => setUseConnectionString(true)}
                    >
                      Connection String
                    </button>
                  </div>
                </div>
                
                {/* Connection String input */}
                {useConnectionString && (
                  <div className="mb-6">
                    <label className="block text-sm text-gray-400 mb-1" htmlFor="database_url">
                      Connection String
                    </label>
                    <input
                      type="text"
                      id="database_url"
                      name="database_url"
                      value={formData.database_url || ''}
                      onChange={handleInputChange}
                      placeholder="e.g. postgresql://user:password@localhost:5432/dbname"
                      className="w-full bg-white/[0.03] border border-white/10 rounded-md px-3 py-2 text-white"
                      required={useConnectionString}
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Format: dialect://username:password@host:port/database
                    </p>
                  </div>
                )}
                
                {/* Individual fields */}
                <div className={cn(
                  "grid grid-cols-1 md:grid-cols-2 gap-4 mb-6",
                  useConnectionString && "opacity-50 pointer-events-none"
                )}>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1" htmlFor="db_type">
                      Database Type
                    </label>
                    <select
                      id="db_type"
                      name="db_type"
                      value={formData.db_type}
                      onChange={handleInputChange}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-md px-3 py-2 text-white"
                      required={!useConnectionString}
                      disabled={useConnectionString}
                    >
                      <option value="postgresql">PostgreSQL</option>
                      <option value="mysql">MySQL</option>
                      <option value="sqlite">SQLite</option>
                      <option value="oracle">Oracle</option>
                      <option value="sqlserver">SQL Server</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-1" htmlFor="db_name">
                      Database Name
                    </label>
                    <input
                      type="text"
                      id="db_name"
                      name="db_name"
                      value={formData.db_name}
                      onChange={handleInputChange}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-md px-3 py-2 text-white"
                      required={!useConnectionString}
                      disabled={useConnectionString}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-1" htmlFor="db_host">
                      Host
                    </label>
                    <input
                      type="text"
                      id="db_host"
                      name="db_host"
                      value={formData.db_host}
                      onChange={handleInputChange}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-md px-3 py-2 text-white"
                      required={!useConnectionString}
                      disabled={useConnectionString}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-1" htmlFor="db_port">
                      Port
                    </label>
                    <input
                      type="number"
                      id="db_port"
                      name="db_port"
                      value={formData.db_port}
                      onChange={handleInputChange}
                      className="w-full bg-white/[0.03] border border-white/10 rounded-md px-3 py-2 text-white"
                      required={!useConnectionString}
                      disabled={useConnectionString}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-1" htmlFor="db_user">
                      Username
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
                      <input
                        type="text"
                        id="db_user"
                        name="db_user"
                        value={formData.db_user}
                        onChange={handleInputChange}
                        className="w-full bg-white/[0.03] border border-white/10 rounded-md pl-10 pr-3 py-2 text-white"
                        required={!useConnectionString}
                        disabled={useConnectionString}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm text-gray-400 mb-1" htmlFor="db_password">
                      Password
                    </label>
                    <div className="relative">
                      <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
                      <input
                        type="password"
                        id="db_password"
                        name="db_password"
                        value={formData.db_password}
                        onChange={handleInputChange}
                        className="w-full bg-white/[0.03] border border-white/10 rounded-md pl-10 pr-3 py-2 text-white"
                        required={!useConnectionString}
                        disabled={useConnectionString}
                      />
                    </div>
                  </div>
                </div>
                
                <button
                  type="submit"
                  disabled={connecting}
                  className={cn(
                    "w-full py-2.5 rounded-md",
                    "bg-gradient-to-r from-indigo-600 to-purple-600 text-white",
                    "hover:opacity-90 transition-opacity",
                    connecting && "opacity-70 cursor-not-allowed"
                  )}
                >
                  {connecting ? 'Connecting...' : 'Connect'}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 