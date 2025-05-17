import axios from 'axios';
// Import all required types using type-only imports
import type { 
  Text2SQLRequest, 
  Text2SQLResponse, 
  DatabaseInfo, 
  DatabaseConnectionRequest,
  DatabaseConnectionResponse,
  DatabaseConfig,
  AgentInfoResponse,
  QueryResult,
  DatabaseStatus
} from '../types/api';

const API_URL = '/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Process a natural language query to SQL
  processSqlQuery: async (request: Text2SQLRequest): Promise<Text2SQLResponse> => {
    console.log('Request object:', request);
    console.log('Stringified request:', JSON.stringify(request));
    const response = await api.post('/process', request);
    return response.data;
  },
  
  // Get database schema (optionally with database URL)
  getDatabaseSchema: async (databaseUrl?: string): Promise<DatabaseInfo> => {
    const params = databaseUrl ? { database_url: databaseUrl } : {};
    const response = await api.get('/schema', { params });
    return response.data;
  },
  
  // Get current database configuration
  getDatabaseConfig: async (): Promise<DatabaseConfig> => {
    const response = await api.get('/database/config');
    return response.data;
  },
  
  // Connect to database (establish persistent connection)
  connectToDatabase: async (
    connectionDetails: DatabaseConnectionRequest
  ): Promise<DatabaseConnectionResponse> => {
    const response = await api.post('/database/connect', connectionDetails);
    return response.data;
  },
  
  // Test database connection (legacy method)
  testDatabaseConnection: async (
    connectionDetails: DatabaseConnectionRequest
  ): Promise<DatabaseConnectionResponse> => {
    const response = await api.post('/database/connect', connectionDetails);
    return response.data;
  },
  
  // Get database connection status
  getDatabaseStatus: async (): Promise<DatabaseStatus> => {
    const response = await api.get('/database/status');
    return response.data;
  },
  
  // Get conversation history
  getConversationHistory: async (conversationId: string): Promise<any[]> => {
    const response = await api.get(`/conversations/${conversationId}`);
    return response.data;
  },
  
  // Get agent information
  getAgentInfo: async (): Promise<AgentInfoResponse> => {
    const response = await api.get('/agent/info');
    return response.data;
  },
  
  // Execute a custom SQL query
  executeCustomSql: async (sql: string, conversationId?: string, databaseUrl?: string): Promise<QueryResult> => {
    const response = await api.post('/execute-custom-sql', {
      sql,
      conversation_id: conversationId,
      database_url: databaseUrl
    });
    return response.data;
  },
}; 