// Request for Text-to-SQL conversion
export interface Text2SQLRequest {
  query: string;
  conversation_id?: string;
  user_id?: string;
  explanation_type?: ExplanationType;
  execute_query?: boolean;
  agent_type?: AgentType;
  database_url?: string;
}

// Response from Text-to-SQL conversion
export interface Text2SQLResponse {
  user_response: UserResponse;
  conversation_id: string;
  timestamp: string;
  enhanced_agent_used: boolean;
}

// Database connection request
export interface DatabaseConnectionRequest {
  db_type: string;
  db_name: string;
  db_user?: string;
  db_password?: string;
  db_host?: string;
  db_port?: number;
  database_url?: string;
}

// Database connection response
export interface DatabaseConnectionResponse {
  success: boolean;
  message: string;
  details?: Record<string, any>;
}

// Database configuration
export interface DatabaseConfig {
  db_type: string;
  db_name: string;
  db_host?: string;
  db_port?: number;
  db_user?: string;
  connection_url?: string;
}

// Agent information response
export interface AgentInfoResponse {
  enhanced_available: boolean;
  current_agent_type: string;
  message: string;
}

// User response
export interface UserResponse {
  user_query: UserQuery;
  intent: IntentOutput;
  sql_generation: SQLGenerationOutput;
  query_result?: QueryResult;
  explanation: UserExplanation;
  conversation_id: string;
  timestamp: string;
}

// User query
export interface UserQuery {
  text: string;
  conversation_id: string;
  user_id?: string;
  timestamp: string;
}

// Intent classification output
export interface IntentOutput {
  intent_type: string;
  confidence: number;
  entities: Record<string, any>;
  clarification_questions?: string[];
}

// SQL generation output
export interface SQLGenerationOutput {
  sql: string;
  status: QueryStatus;
  confidence: number;
  warnings: string[];
  alternative_queries?: string[];
}

// Query result
export interface QueryResult {
  status: QueryStatus;
  columns?: string[];
  column_names?: string[];
  rows: Record<string, any>[];
  row_count?: number;
  affected_rows?: number;
  execution_time?: number;
  error_message?: string;
  warnings?: string[];
}

// Explanation
export interface UserExplanation {
  text: string;
  explanation_type: ExplanationType;
  type?: ExplanationType;
  sql_breakdown?: Record<string, string>;
  additional_notes?: string[];
  referenced_concepts?: string[];
}

// Database information
export interface DatabaseInfo {
  name: string;
  description: string;
  tables: TableInfo[];
  relationships: Relationship[];
}

// Database type information
export interface DatabaseType {
  id: string;
  name: string;
  description: string;
  defaultPort?: number;
  requiresAuth: boolean;
  requiresHost: boolean;
}

// Table information
export interface TableInfo {
  name: string;
  description: string;
  columns: ColumnInfo[];
  // Rename any schema field if it exists
  // This avoids conflicts with BaseModel.schema
}

// Column information
export interface ColumnInfo {
  name: string;
  data_type: string;
  description: string;
  nullable: boolean;
  primary_key: boolean;
  foreign_key?: string;
}

// Database relationship
export interface Relationship {
  source_table: string;
  source_column: string;
  target_table: string;
  target_column: string;
  relationship_type: string;
}

// Query status enum
export enum QueryStatus {
  SUCCESS = "SUCCESS",
  ERROR = "ERROR",
  WARNING = "WARNING",
}

// Agent type enum
export enum AgentType {
  BASE = "base",
  ENHANCED = "enhanced"
}

// Explanation type enum
export enum ExplanationType {
  SIMPLIFIED = "SIMPLIFIED",
  TECHNICAL = "TECHNICAL",
  EDUCATIONAL = "EDUCATIONAL",
  BRIEF = "BRIEF",
}

// Database status
export interface DatabaseStatus {
  connected: boolean;
  message: string;
  dialect?: string;
  database_url_hash?: number;
} 