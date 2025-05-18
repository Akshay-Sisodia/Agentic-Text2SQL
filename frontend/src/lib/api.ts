// Base API URL - use deployed API URL in production
const API_BASE_URL = import.meta.env.PROD 
  ? 'https://agentic-text2sql-api.onrender.com/api/v1' 
  : 'http://localhost:8000/api/v1';

export interface DatabaseConnectionInfo {
  connected: boolean;
  dbName: string | null;
  dbType: string | null;
  message: string;
  details?: Record<string, any>;
}

// Query history interface
export interface HistoryItem {
  id: string;
  query: string;
  sql: string;
  timestamp: string;
  conversation_id?: string;
}

export interface DatabaseConnectionRequest {
  db_type?: string;
  db_name?: string;
  db_user?: string;
  db_password?: string;
  db_host?: string;
  db_port?: number;
  database_url?: string;
}

export interface DatabaseConnectionResponse {
  success: boolean;
  message: string;
  details?: Record<string, any>;
}

export interface CustomSqlRequest {
  sql: string;
  database_url?: string;
  conversation_id?: string;
  user_id?: string;
}

export interface AgentInfoResponse {
  enhanced_available: boolean;
  current_agent_type: string;
  message: string;
}

export type ExplanationType = 'TECHNICAL' | 'SIMPLIFIED' | 'EDUCATIONAL' | 'BRIEF';

export interface QueryResult {
  status: "SUCCESS" | "ERROR" | "PENDING" | "CANCELLED";
  rows?: Record<string, any>[];
  row_count?: number;
  column_names?: string[];
  columns?: string[];
  execution_time?: number;
  error_message?: string;
  warnings: string[];
}

export interface UserExplanation {
  text: string;
  explanation_type: ExplanationType;
  referenced_concepts?: string[];
}

export interface UserResponse {
  query: string;
  sql: string;
  explanation?: UserExplanation;
  result?: QueryResult;
  intent?: any;
  error?: string;
  suggested_followups?: string[];
  metadata?: Record<string, any>;
}

interface DatabaseStatusResponse {
  connected: boolean;
  dialect?: string;
  database_url_hash?: number; 
  is_sample_db?: boolean;
  message: string;
}

/**
 * Check the current database connection status
 */
export async function getDatabaseStatus(): Promise<DatabaseStatusResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/database/status`);
    
    if (!response.ok) {
      return {
        connected: false,
        message: 'Failed to connect to backend server'
      };
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error checking database status:', error);
    return {
      connected: false,
      message: 'Error connecting to backend server'
    };
  }
}

/**
 * Get database configuration
 */
export async function getDatabaseConfig() {
  try {
    const response = await fetch(`${API_BASE_URL}/database/config`);
    if (!response.ok) {
      throw new Error('Failed to get database configuration');
    }
    return await response.json();
  } catch (error) {
    console.error('Error getting database config:', error);
    throw error;
  }
}

/**
 * Connect to a database
 */
export async function connectToDatabase(
  connectionData: DatabaseConnectionRequest
): Promise<DatabaseConnectionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/database/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(connectionData),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return {
        success: false,
        message: errorData.message || 'Failed to connect to database',
        details: errorData.details
      };
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error connecting to database:', error);
    return {
      success: false,
      message: 'Error connecting to database server'
    };
  }
}

/**
 * Get database schema information
 */
export async function getDatabaseSchema(databaseUrl?: string) {
  try {
    const url = new URL(`${API_BASE_URL}/schema`, window.location.origin);
    if (databaseUrl) {
      url.searchParams.append('database_url', databaseUrl);
    }
    
    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error('Failed to fetch schema');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching database schema:', error);
    throw error;
  }
}

/**
 * Process a text-to-SQL query
 */
export async function processQuery(query: string, conversationId?: string, explanationType: ExplanationType = 'SIMPLIFIED') {
  try {
    const response = await fetch(`${API_BASE_URL}/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query,
        conversation_id: conversationId,
        explanation_type: explanationType,
        execute_query: true
      }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to process query');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error processing query:', error);
    throw error;
  }
}

/**
 * Process a simple query (GET endpoint)
 */
export async function processSimpleQuery(query: string, conversationId?: string, databaseUrl?: string, explanationType: ExplanationType = 'SIMPLIFIED') {
  try {
    const url = new URL(`${API_BASE_URL}/query`, window.location.origin);
    url.searchParams.append('query', query);
    
    if (conversationId) {
      url.searchParams.append('conversation_id', conversationId);
    }
    
    if (databaseUrl) {
      url.searchParams.append('database_url', databaseUrl);
    }
    
    url.searchParams.append('explanation_type', explanationType);
    
    const response = await fetch(url.toString());
    
    if (!response.ok) {
      throw new Error('Failed to process query');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error processing simple query:', error);
    throw error;
  }
}

/**
 * Execute custom SQL
 */
export async function executeCustomSql(request: CustomSqlRequest) {
  try {
    const response = await fetch(`${API_BASE_URL}/execute-custom-sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error('Failed to execute custom SQL');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error executing custom SQL:', error);
    throw error;
  }
}

/**
 * Get conversation history
 */
export async function getConversationHistory(conversationId: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch conversation history');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching conversation history:', error);
    throw error;
  }
}

/**
 * Get agent information
 */
export async function getAgentInfo(): Promise<AgentInfoResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/agent/info`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch agent information');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching agent information:', error);
    throw error;
  }
}

/**
 * Get query history
 */
export async function getQueryHistory(): Promise<HistoryItem[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/history`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch query history');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching query history:', error);
    throw error;
  }
}

/**
 * Delete a query history item
 */
export async function deleteQueryHistory(id: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/history/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete history item');
    }
  } catch (error) {
    console.error('Error deleting history item:', error);
    throw error;
  }
}

/**
 * Create an SSE connection for status updates
 * Returns an EventSource that can be used to listen for status updates
 */
export function createStatusUpdateStream(): EventSource {
  const eventSource = new EventSource(`${API_BASE_URL}/status/stream`);
  
  eventSource.onerror = (error) => {
    console.error('Error in status update stream:', error);
    // Auto-reconnect is handled by the browser
  };
  
  return eventSource;
} 