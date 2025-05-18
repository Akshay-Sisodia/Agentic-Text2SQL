import { useState, useEffect, useCallback } from 'react';
import { 
  getDatabaseStatus, 
  connectToDatabase,
  getAgentInfo
} from './api';
import type { 
  DatabaseConnectionRequest,
  AgentInfoResponse,
  DatabaseConnectionResponse
} from './api';

/**
 * Interface for database connection information
 */
export interface DatabaseConnectionInfo {
  connected: boolean;
  dbName: string | null;
  dbType: string | null;
  message: string;
  details?: Record<string, any>;
}

/**
 * Custom hook for managing database connection
 */
export function useDatabaseConnection() {
  const [connectionInfo, setConnectionInfo] = useState<DatabaseConnectionInfo>({
    connected: false,
    dbName: null,
    dbType: null,
    message: 'Checking connection...'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Function to check database connection status
  const checkConnection = useCallback(async () => {
    setLoading(true);
    try {
      const status = await getDatabaseStatus();
      
      // Map status response to our connection info format
      setConnectionInfo({
        connected: status.connected,
        dbName: status.is_sample_db ? 'Sample Database' : 
                (status.dialect ? `${status.dialect} Database` : null),
        dbType: status.dialect || null,
        message: status.message || '',
        details: status
      });
      
      setError(null);
    } catch (err) {
      setConnectionInfo({
        connected: false,
        dbName: null,
        dbType: null,
        message: 'Failed to connect to server'
      });
      setError('Error checking connection status');
    } finally {
      setLoading(false);
    }
  }, []);

  // Function to connect to a database
  const connect = useCallback(async (connectionData: DatabaseConnectionRequest): Promise<DatabaseConnectionResponse> => {
    setLoading(true);
    try {
      const result = await connectToDatabase(connectionData);
      
      if (result.success) {
        // After successful connection, fetch updated status
        await checkConnection();
      } else {
        setError(result.message);
      }
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error connecting to database';
      setError(errorMessage);
      return { 
        success: false, 
        message: errorMessage 
      };
    } finally {
      setLoading(false);
    }
  }, [checkConnection]);

  // Check connection status on component mount
  useEffect(() => {
    checkConnection();
    
    // Set up periodic connection check (every 30 seconds)
    const intervalId = setInterval(() => {
      checkConnection();
    }, 30000);
    
    return () => clearInterval(intervalId);
  }, [checkConnection]);

  return {
    connectionInfo,
    loading,
    error,
    checkConnection,
    connect
  };
}

/**
 * Custom hook for agent information
 */
export function useAgentInfo() {
  const [agentInfo, setAgentInfo] = useState<AgentInfoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAgentInfo = useCallback(async () => {
    setLoading(true);
    try {
      const info = await getAgentInfo();
      setAgentInfo(info);
      setError(null);
    } catch (err) {
      setError('Failed to fetch agent information');
      setAgentInfo(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAgentInfo();
  }, [fetchAgentInfo]);

  return {
    agentInfo,
    loading,
    error,
    refresh: fetchAgentInfo
  };
}

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, [query]);

  return matches;
} 