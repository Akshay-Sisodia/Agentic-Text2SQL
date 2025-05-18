import React, { useEffect, useRef, useCallback, useState } from "react";
import { cn } from "@/lib/utils";
import { v4 as uuid } from "uuid";
import { useNavigate } from "react-router-dom";
import {
  CircleUserRound,
  SendIcon,
  LoaderIcon,
  Database,
  Code,
  Table,
  HelpCircle,
  MessageSquare,
  Zap,
  Download,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  processQuery, 
  getDatabaseSchema, 
  getConversationHistory,
  createStatusUpdateStream
} from "@/lib/api";
import type { 
  UserExplanation, 
  QueryResult
} from "@/lib/api";
import { useDatabaseConnection } from "@/lib/hooks";

// Types that match our API schemas
interface UserQuery {
  text: string;
  conversation_id?: string;
  user_id?: string;
  timestamp?: string;
  metadata?: Record<string, any>;
}

// Using imported types from API module
interface SQLGenerationOutput {
  sql: string;
  explanation?: string;
  confidence: number;
  alternatives: string[];
  warnings: string[];
  metadata: Record<string, any>;
  referenced_tables: string[];
  referenced_columns: string[];
  validation_issues: string[];
  error_message?: string;
}

interface UserResponse {
  user_query: UserQuery;
  intent?: any;
  sql_generation?: SQLGenerationOutput;
  query_result?: QueryResult;
  explanation?: UserExplanation;
  suggested_followups: string[];
  conversation_id?: string;
  timestamp?: string;
  metadata: Record<string, any>;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  response?: UserResponse;
  schema?: any;
  isDirectCommand?: boolean;
}

interface UseAutoResizeTextareaProps {
  minHeight: number;
  maxHeight?: number;
}

function useAutoResizeTextarea({
  minHeight,
  maxHeight,
}: UseAutoResizeTextareaProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(
    (reset?: boolean) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      if (reset) {
        textarea.style.height = `${minHeight}px`;
        return;
      }

      textarea.style.height = `${minHeight}px`;
      const newHeight = Math.max(
        minHeight,
        Math.min(textarea.scrollHeight, maxHeight ?? Number.POSITIVE_INFINITY)
      );

      textarea.style.height = `${newHeight}px`;
    },
    [minHeight, maxHeight]
  );

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = `${minHeight}px`;
    }
  }, [minHeight]);

  useEffect(() => {
    const handleResize = () => adjustHeight();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [adjustHeight]);

  return { textareaRef, adjustHeight };
}

interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  containerClassName?: string;
  showRing?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, containerClassName, showRing = true, ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);
    
    return (
      <div className={cn("relative", containerClassName)}>
        <textarea
          className={cn(
            "flex min-h-[80px] w-full rounded-md border border-white/10 bg-white/[0.03] px-3 py-2 text-sm",
            "transition-all duration-200 ease-in-out",
            "placeholder:text-white/30 placeholder:font-sans",
            "resize-none",
            "disabled:cursor-not-allowed disabled:opacity-50",
            showRing ? "focus-visible:outline-none focus-visible:ring-0 focus-visible:ring-offset-0" : "",
            className
          )}
          ref={ref}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          {...props}
        />
        
        {showRing && isFocused && (
          <motion.span 
            className="absolute inset-0 rounded-md pointer-events-none ring-2 ring-offset-0 ring-violet-500/30"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          />
        )}
      </div>
    )
  }
)

Textarea.displayName = "Textarea";

interface CommandSuggestion {
  icon: React.ReactNode;
  label: string;
  description: string;
  prefix: string;
}

export function SQLChatbot() {
  const [value, setValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [activeSuggestion, setActiveSuggestion] = useState<number>(-1);
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 60,
    maxHeight: 200,
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const commandPaletteRef = useRef<HTMLDivElement>(null);
  const { connectionInfo } = useDatabaseConnection();
  const [statusEvents, setStatusEvents] = useState<{message: string, timestamp: Date}[]>([]);
  const [showStatus, setShowStatus] = useState(true);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    // Ensure we scroll to bottom when messages change
    scrollToBottom();
  }, [messages]);
  
  // Auto-hide status indicator after 5 seconds if it hasn't changed
  useEffect(() => {
    if (statusEvents.length > 0) {
      setShowStatus(true);
      const timer = setTimeout(() => {
        setShowStatus(false);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [statusEvents]);
  
  // Connect to status updates stream
  useEffect(() => {
    const connectStatusStream = () => {
      const eventSource = createStatusUpdateStream();
      
      eventSource.addEventListener('status_update', (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Only add status messages that indicate a change or initial connection
          if (data.status_changed === true || data.message.includes('Connected to status stream')) {
            setStatusEvents(prev => {
              // Limit to only the 2 most recent status events
              const newEvents = [...prev, { 
                message: data.message,
                timestamp: new Date()
              }];
              return newEvents.slice(-2);
            });
          }
        } catch (error) {
          console.error('Error parsing status event:', error);
        }
      });
      
      eventSource.onerror = (err) => {
        console.error("Status stream error:", err);
        // Simple retry with exponential back-off
        setTimeout(() => {
          eventSource.close();
          setStatusEvents(prev => [
            ...prev,
            { message: "Re-connecting to status stream...", timestamp: new Date() },
          ]);
          // open a fresh connection
          connectStatusStream();
        }, 2000);
      };
      
      return eventSource;
    };
    
    const eventSource = connectStatusStream();
    
    return () => {
      eventSource.close();
    };
  }, []);
  
  // Load conversation from URL parameter
  useEffect(() => {
    const abort = new AbortController();
    const loadConversation = async () => {
      try {
        setIsLoading(true);
        // Check for conversation_id in URL
        const params = new URLSearchParams(window.location.search);
        const conversationId = params.get('conversation');
        
        if (conversationId) {
          const history = await getConversationHistory(conversationId);
          
          if (history && history.length > 0) {
            // Set the conversation ID
            setCurrentConversationId(conversationId);
            
            // Convert history items to messages
            const convertedMessages: Message[] = [];
            
            // Process each history item
            history.forEach((item: any) => {
              // First, add the user message
              if (item.user_query && typeof item.user_query === 'object') {
                convertedMessages.push({
                  id: uuid(),
                  role: "user",
                  content: item.user_query.text || "",
                  timestamp: new Date(item.timestamp || Date.now()),
                });
              } else if (typeof item.query === 'string') {
                // Fallback for older format
                convertedMessages.push({
                  id: uuid(),
                  role: "user",
                  content: item.query,
                  timestamp: new Date(item.timestamp || Date.now()),
                });
              }
              
              // Then add the assistant response
              convertedMessages.push({
                id: uuid(),
                role: "assistant",
                content: item.explanation?.text || "Here's the SQL for your query.",
                timestamp: new Date(item.timestamp || Date.now()),
                response: {
                  user_query: item.user_query || { text: item.query || "" },
                  sql_generation: item.sql_generation || { 
                    sql: item.sql || "", 
                    confidence: 1, 
                    alternatives: [], 
                    warnings: [], 
                    metadata: {}, 
                    referenced_tables: [], 
                    referenced_columns: [], 
                    validation_issues: [] 
                  },
                  query_result: item.query_result || item.result,
                  explanation: item.explanation,
                  suggested_followups: item.suggested_followups || [],
                  conversation_id: item.conversation_id || conversationId,
                  timestamp: item.timestamp,
                  metadata: item.metadata || {}
                },
              });
            });
            
            // Set messages
            if (convertedMessages.length > 0) {
              setMessages(convertedMessages);
              console.log("Loaded conversation history:", convertedMessages);
            }
          }
        }
      } catch (error) {
        console.error("Error loading conversation:", error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadConversation();
    
    return () => abort.abort();
  }, [window.location.search]);

  const commandSuggestions: CommandSuggestion[] = [
    { 
      icon: <Table className="w-4 h-4" />, 
      label: "Show Schema", 
      description: "Display database schema information", 
      prefix: "/schema" 
    },
    { 
      icon: <Database className="w-4 h-4" />, 
      label: "Connect DB", 
      description: "Connect to a database", 
      prefix: "/connect" 
    },
    { 
      icon: <HelpCircle className="w-4 h-4" />, 
      label: "Help", 
      description: "Show help information", 
      prefix: "/help" 
    },
  ];

  // Use effect to handle command suggestions
  useEffect(() => {
    if (value.startsWith('/') && !value.includes(' ')) {
      setShowCommandPalette(true);
      
      const matchingSuggestionIndex = commandSuggestions.findIndex(
        (cmd) => cmd.prefix.startsWith(value)
      );
      
      if (matchingSuggestionIndex >= 0) {
        setActiveSuggestion(matchingSuggestionIndex);
      } else {
        setActiveSuggestion(-1);
      }
    } else {
      setShowCommandPalette(false);
    }
  }, [value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showCommandPalette) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveSuggestion(prev => 
          prev < commandSuggestions.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveSuggestion(prev => 
          prev > 0 ? prev - 1 : commandSuggestions.length - 1
        );
      } else if (e.key === 'Tab' || e.key === 'Enter') {
        e.preventDefault();
        if (activeSuggestion >= 0) {
          const selectedCommand = commandSuggestions[activeSuggestion];
          setValue(selectedCommand.prefix + ' ');
          setShowCommandPalette(false);
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setShowCommandPalette(false);
      }
    } else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim()) {
        handleSendMessage();
      }
    }
  };

  const handleDirectCommand = async (command: string) => {
    const userMessage: Message = {
      id: uuid(),
      role: "user",
      content: command,
      timestamp: new Date(),
      isDirectCommand: true,
    };
    
    setMessages(prev => [...prev, userMessage]);
    setValue("");
    adjustHeight(true);
    setIsLoading(true);
    
    try {
      if (command.startsWith('/schema')) {
        // Fetch schema information
        const schemaData = await getDatabaseSchema();
        
        // Create assistant message with schema data
        const assistantMessage: Message = {
          id: uuid(),
          role: "assistant",
          content: "Here's your database schema information:",
          timestamp: new Date(),
          schema: schemaData,
          isDirectCommand: true,
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      } 
      else if (command.startsWith('/connect')) {
        // Redirect to database connections page
        navigate('/dashboard?tab=connections');
        
        // Add a message indicating redirection
        const assistantMessage: Message = {
          id: uuid(),
          role: "assistant",
          content: "Redirecting to database connections...",
          timestamp: new Date(),
          isDirectCommand: true,
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      }
      else if (command.startsWith('/help')) {
        // Show help information
        const assistantMessage: Message = {
          id: uuid(),
          role: "assistant",
          content: "Here are some ways to interact with the Text-to-SQL chatbot:",
          timestamp: new Date(),
          isDirectCommand: true,
          response: {
            user_query: { text: "/help" },
            explanation: {
              text: "Text-to-SQL Help",
              explanation_type: "SIMPLIFIED",
              referenced_concepts: []
            },
            query_result: {
              status: "SUCCESS",
              rows: [
                { command: "Ask a question", description: "Type a natural language question about your data" },
                { command: "/schema", description: "View your database schema" },
                { command: "/connect", description: "Connect to a database" },
                { command: "/help", description: "Show this help information" }
              ],
              column_names: ["command", "description"],
              row_count: 4,
              columns: ["command", "description"],
              execution_time: 0,
              warnings: []
            },
            suggested_followups: [
              "Show me all tables in the database",
              "What are the columns in the users table?",
              "How many customers made a purchase last month?"
            ],
            metadata: {}
          }
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error("Error handling direct command:", error);
      
      // Add an error message
      setMessages(prev => [
        ...prev,
        {
          id: uuid(),
          role: "assistant",
          content: `Error: Unable to execute the command. ${connectionInfo.connected ? "" : "Please make sure you're connected to a database."}`,
          timestamp: new Date(),
          isDirectCommand: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!value.trim()) return;
    
    // Process direct commands without going through the LLM
    if (value.trim().startsWith('/')) {
      await handleDirectCommand(value.trim());
      return;
    }
    
    const userMessage: Message = {
      id: uuid(),
      role: "user",
      content: value.trim(),
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setValue("");
    adjustHeight(true);
    setIsLoading(true);
    
    try {
      // Make API call to process the query
      const response = await processQuery(value.trim(), currentConversationId || undefined);
      
      // Update the conversation ID if we got a new one
      if (response.conversation_id) {
        setCurrentConversationId(response.conversation_id);
      }
      
      // Create the assistant message
      const assistantMessage: Message = {
        id: uuid(),
        role: "assistant",
        content: response.user_response.explanation?.text || "Here's the SQL for your query.",
        timestamp: new Date(),
        response: response.user_response,
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      
      // Add an error message
      setMessages(prev => [
        ...prev,
        {
          id: uuid(),
          role: "assistant",
          content: "Sorry, there was an error processing your query. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const selectCommandSuggestion = (index: number) => {
    const selectedCommand = commandSuggestions[index];
    setValue(selectedCommand.prefix + ' ');
    setShowCommandPalette(false);
  };

  const downloadCSV = (results: QueryResult) => {
    if (!results.rows || !results.column_names) return;
    
    // Create CSV header row
    let csv = results.column_names.join(',') + '\n';
    
    // Add data rows
    results.rows.forEach(row => {
      const rowValues = results.column_names!.map(column => {
        // Handle values that might contain commas or quotes
        const value = row[column] !== undefined ? String(row[column]) : '';
        if (value.includes(',') || value.includes('"') || value.includes('\n')) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      });
      csv += rowValues.join(',') + '\n';
    });
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    // Set download attributes
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    link.setAttribute('href', url);
    link.setAttribute('download', `query-results-${timestamp}.csv`);
    link.style.visibility = 'hidden';
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const renderSQLCode = (sql: string) => {
    return (
      <div className="rounded-md bg-black/80 border border-white/5 p-3 my-2 overflow-auto max-h-[250px]">
        <pre className="text-indigo-300 text-sm font-mono">{sql}</pre>
      </div>
    );
  };

  const renderQueryResults = (results: QueryResult) => {
    if (results.status !== "SUCCESS" || !results.rows || results.rows.length === 0) {
      return (
        <div className="bg-red-900/20 border border-red-500/20 text-red-300 p-3 rounded-md my-2">
          {results.error_message || "No results returned."}
        </div>
      );
    }

    return (
      <div>
        <div className="flex justify-between items-center mb-2">
          <div className="text-xs text-gray-400">
            {results.row_count} row{results.row_count !== 1 ? 's' : ''} returned in {results.execution_time?.toFixed(3) || 0}s
          </div>
          <motion.button
            className="flex items-center gap-1 px-2 py-1 bg-white/[0.05] hover:bg-white/[0.1] rounded-md text-emerald-300 text-xs transition-colors"
            onClick={() => downloadCSV(results)}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Download className="w-3 h-3" />
            <span>Download CSV</span>
          </motion.button>
        </div>
        <div className="rounded-md border border-white/5 my-2 overflow-auto max-h-[350px]">
          <table className="min-w-full divide-y divide-white/10">
            <thead className="bg-white/[0.03]">
              <tr>
                {results.column_names?.map((column, i) => (
                  <th 
                    key={i}
                    className="px-4 py-2 text-left text-xs font-medium text-indigo-300 uppercase tracking-wider"
                  >
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-transparent divide-y divide-white/10">
              {results.rows.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-white/[0.02] transition-colors">
                  {results.column_names?.map((column, colIndex) => (
                    <td key={colIndex} className="px-4 py-2 whitespace-nowrap text-sm text-gray-300">
                      {String(row[column] !== undefined ? row[column] : '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderExplanation = (explanation: UserExplanation) => {
    return (
      <div className="space-y-3">
        <p className="text-gray-300 text-sm whitespace-pre-wrap">{explanation.text}</p>
        
        {explanation.referenced_concepts && explanation.referenced_concepts.length > 0 && (
          <div className="mt-2">
            <h4 className="text-xs font-medium mb-1.5 text-gray-400">Related Concepts</h4>
            <div className="flex flex-wrap gap-1.5">
              {explanation.referenced_concepts.map((concept, i) => (
                <span key={i} className="px-1.5 py-0.5 text-[10px] bg-indigo-500/20 text-indigo-300 rounded-full">
                  {concept}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderSchemaInfo = (schema: any) => {
    if (!schema || !schema.tables || schema.tables.length === 0) {
      return (
        <div className="bg-amber-900/20 border border-amber-500/20 text-amber-300 p-3 rounded-md my-2 text-sm">
          No schema information available. Make sure you're connected to a database.
        </div>
      );
    }

    return (
      <div className="space-y-4 my-2">
        {schema.tables.map((table: any, index: number) => (
          <div key={index} className="rounded-md border border-indigo-500/20 bg-indigo-900/10 overflow-hidden">
            <div className="bg-indigo-900/30 px-3 py-1.5 text-sm font-medium text-indigo-200 flex items-center justify-between">
              <span>{table.name}</span>
              {table.row_count !== undefined && (
                <span className="text-[10px] text-indigo-300">~{table.row_count} rows</span>
              )}
            </div>
            <div className="p-1">
              <table className="w-full text-xs">
                <thead className="bg-black/20">
                  <tr>
                    <th className="px-3 py-1.5 text-left text-[10px] font-medium text-indigo-300">Column</th>
                    <th className="px-3 py-1.5 text-left text-[10px] font-medium text-indigo-300">Type</th>
                    <th className="px-3 py-1.5 text-left text-[10px] font-medium text-indigo-300">Attributes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-indigo-900/20">
                  {table.columns.map((column: any, colIndex: number) => (
                    <tr key={colIndex} className="hover:bg-indigo-900/10">
                      <td className="px-3 py-1.5 whitespace-nowrap text-indigo-200 font-mono">
                        {column.name}
                        {column.primary_key && (
                          <span className="ml-1.5 px-1 py-0.5 bg-indigo-900/40 text-indigo-300 text-[10px] rounded">PK</span>
                        )}
                      </td>
                      <td className="px-3 py-1.5 whitespace-nowrap text-gray-300">{column.data_type}</td>
                      <td className="px-3 py-1.5 whitespace-nowrap text-gray-400">
                        {!column.nullable && <span className="mr-1.5">NOT NULL</span>}
                        {column.foreign_key && <span>→ {column.foreign_key}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
        
        {schema.relationships && schema.relationships.length > 0 && (
          <div className="rounded-md border border-purple-500/20 bg-purple-900/10 overflow-hidden mt-3">
            <div className="bg-purple-900/30 px-3 py-1.5 text-sm font-medium text-purple-200">
              Relationships
            </div>
            <div className="p-1">
              <table className="w-full text-xs">
                <thead className="bg-black/20">
                  <tr>
                    <th className="px-3 py-1.5 text-left text-[10px] font-medium text-purple-300">Source</th>
                    <th className="px-3 py-1.5 text-left text-[10px] font-medium text-purple-300">Target</th>
                    <th className="px-3 py-1.5 text-left text-[10px] font-medium text-purple-300">Type</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-purple-900/20">
                  {schema.relationships.map((rel: any, relIndex: number) => (
                    <tr key={relIndex} className="hover:bg-purple-900/10">
                      <td className="px-3 py-1.5 whitespace-nowrap text-purple-200 font-mono">
                        {rel.source_table}.{rel.source_column}
                      </td>
                      <td className="px-3 py-1.5 whitespace-nowrap text-purple-200 font-mono">
                        {rel.target_table}.{rel.target_column}
                      </td>
                      <td className="px-3 py-1.5 whitespace-nowrap text-gray-300">
                        {rel.relationship_type}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderSuggestedFollowups = (followups: string[]) => {
    if (!followups.length) return null;
    
    return (
      <div className="mt-2">
        <p className="text-xs text-gray-400 mb-1.5">Suggested follow-ups:</p>
        <div className="flex flex-wrap gap-1.5">
          {followups.map((followup, index) => (
            <button
              key={index}
              className="px-2 py-1 bg-white/[0.03] hover:bg-white/[0.06] text-gray-300 border border-white/5 text-xs rounded-md transition-colors"
              onClick={() => {
                setValue(followup);
                adjustHeight();
              }}
            >
              {followup}
            </button>
          ))}
        </div>
      </div>
    );
  };

  const renderStatusIndicator = () => {
    if (statusEvents.length === 0 || !showStatus) return null;
    
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <motion.div 
          className="bg-black/80 backdrop-blur-sm border border-white/10 rounded-md shadow-lg p-2"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
        >
          <div className="flex items-center gap-2 mb-1">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-xs font-medium text-gray-300">System Status</span>
          </div>
          <div className="space-y-1.5 max-h-32 overflow-auto">
            {statusEvents.map((event, i) => (
              <div key={i} className="text-xs text-gray-400">
                <span className="text-gray-500">{event.timestamp.toLocaleTimeString()}</span>
                <span className="ml-2">{event.message}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full relative">
      {/* Messages container */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 pb-4 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-2 md:px-4">
            <div className="max-w-2xl w-full p-2 md:p-4">
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2, duration: 0.5 }}
                className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center"
              >
                <Database className="w-8 h-8 text-white" />
              </motion.div>
              
              <h1 className="text-xl md:text-2xl font-bold mb-3 bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent">
                Welcome to Text-to-SQL
              </h1>
              <p className="text-gray-400 mb-6 text-sm md:text-base max-w-lg mx-auto">
                Ask questions about your data in plain English and get SQL queries, results, and explanations.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 md:gap-3 max-w-2xl mx-auto">
                {commandSuggestions.map((suggestion) => (
                  <motion.div 
                    key={suggestion.prefix}
                    className="p-2 md:p-3 bg-white/[0.04] backdrop-blur-sm border border-white/[0.1] rounded-lg flex flex-col items-center gap-1 md:gap-2 cursor-pointer hover:bg-white/[0.07] transition-colors"
                    onClick={() => setValue(suggestion.prefix + " ")}
                    whileHover={{ y: -2, scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    transition={{ 
                      type: "spring", 
                      stiffness: 500,
                      damping: 30
                    }}
                  >
                    <div className="p-2 bg-indigo-500/20 text-indigo-400 rounded-lg">
                      {suggestion.icon}
                    </div>
                    <div className="text-center">
                      <p className="font-medium text-white text-sm mb-0.5">{suggestion.label}</p>
                      <p className="text-xs text-gray-400">{suggestion.description}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
              
              <motion.div 
                className="mt-6 md:mt-8 flex justify-center"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.5 }}
              >
                <div className="inline-flex items-center gap-2 text-xs text-gray-400 border border-white/10 px-3 py-2 md:px-4 md:py-2 rounded-full">
                  <Zap className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Type a question below to get started</span>
                </div>
              </motion.div>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <motion.div
              key={message.id}
              className={cn(
                "py-2 md:py-3",
                index > 0 && "border-t border-white/[0.05]"
              )}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1, duration: 0.3 }}
            >
              <div className={cn(
                "flex gap-2 md:gap-3 max-w-[98%] md:max-w-[95%] mx-auto px-0 md:px-1",
                message.role === "user" ? "flex-row-reverse" : "flex-row"
              )}>
                <div className="mt-1 flex-shrink-0 flex flex-col items-center">
                  {message.role === "user" ? (
                    <>
                      <div className="w-6 h-6 md:w-8 md:h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                        <CircleUserRound className="w-4 h-4 md:w-5 md:h-5" />
                      </div>
                      <span className="text-[10px] md:text-xs text-indigo-400 mt-1">You</span>
                    </>
                  ) : (
                    <>
                      <div className="w-6 h-6 md:w-8 md:h-8 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400">
                        <Database className="w-4 h-4 md:w-5 md:h-5" />
                      </div>
                      <span className="text-[10px] md:text-xs text-violet-400 mt-1">AI</span>
                    </>
                  )}
                </div>
                <div className={cn(
                  "flex-1 max-w-[85%] text-sm md:text-base p-2 md:p-3 rounded-lg",
                  message.role === "user" 
                    ? "ml-auto bg-indigo-900/20 border border-indigo-500/20" 
                    : "mr-auto bg-violet-900/20 border border-violet-500/20"
                )}>
                  <div className="prose prose-invert prose-sm md:prose-base max-w-none">
                    {message.role === "user" ? (
                      <p className="text-white">{message.content}</p>
                    ) : (
                      <div>
                        {(message.response as any)?.sql_generation?.sql || (message.response as any)?.sql ? (
                          <div className="mb-3 md:mb-4">
                            <div className="flex items-center gap-1 md:gap-2 mb-1 md:mb-2">
                              <Code className="w-3 h-3 md:w-4 md:h-4 text-indigo-400" />
                              <h4 className="text-xs md:text-sm font-medium text-indigo-300 m-0">
                                Generated SQL
                              </h4>
                            </div>
                            <div className="overflow-x-auto">
                            {renderSQLCode((message.response as any)?.sql_generation?.sql || (message.response as any)?.sql || "")}
                            </div>
                          </div>
                        ) : null}
                        
                        {(message.response as any)?.query_result || (message.response as any)?.result ? (
                          <div className="mb-3 md:mb-4">
                            <div className="flex items-center gap-1 md:gap-2 mb-1 md:mb-2">
                              <Table className="w-3 h-3 md:w-4 md:h-4 text-emerald-400" />
                              <h4 className="text-xs md:text-sm font-medium text-emerald-300 m-0">
                                Query Results
                              </h4>
                            </div>
                            <div className="overflow-x-auto">
                            {renderQueryResults((message.response as any)?.query_result || (message.response as any)?.result)}
                            </div>
                          </div>
                        ) : null}
                        
                        {message.response?.explanation ? (
                          <div className="mb-3 md:mb-4">
                            <div className="flex items-center gap-1 md:gap-2 mb-1 md:mb-2">
                              <MessageSquare className="w-3 h-3 md:w-4 md:h-4 text-violet-400" />
                              <h4 className="text-xs md:text-sm font-medium text-violet-300 m-0">
                                Explanation
                              </h4>
                            </div>
                            {renderExplanation(message.response.explanation)}
                          </div>
                        ) : null}
                        
                        {message.schema && (
                          <div className="mb-3 md:mb-4">
                            <div className="flex items-center gap-1 md:gap-2 mb-1 md:mb-2">
                              <Database className="w-3 h-3 md:w-4 md:h-4 text-blue-400" />
                              <h4 className="text-xs md:text-sm font-medium text-blue-300 m-0">
                                Schema Information
                              </h4>
                            </div>
                            <div className="overflow-x-auto">
                            {renderSchemaInfo(message.schema)}
                            </div>
                          </div>
                        )}
                        
                        {message.response?.suggested_followups &&
                          message.response.suggested_followups.length > 0 && (
                            <div className="mt-4 md:mt-6">
                              {renderSuggestedFollowups(message.response.suggested_followups)}
                            </div>
                          )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="p-2 md:p-4 border-t border-white/10">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
        >
          <div className="relative">
            <Textarea
              ref={textareaRef}
              value={value}
              onChange={(e) => {
                setValue(e.target.value);
                adjustHeight();
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your database..."
              className="pr-12 text-sm md:text-base"
              disabled={isLoading}
            />
            <motion.div
              className="absolute right-3 bottom-2.5"
              animate={isLoading ? { rotate: 360 } : {}}
              transition={isLoading ? { repeat: Infinity, duration: 1, ease: "linear" } : {}}
            >
              <button 
                type="submit"
                disabled={isLoading}
                className={cn(
                  "rounded-md p-1.5 bg-violet-600 text-white flex items-center justify-center focus:outline-none",
                  isLoading && "opacity-70"
                )}
              >
                {isLoading ? <LoaderIcon className="w-4 h-4" /> : <SendIcon className="w-4 h-4" />}
              </button>
            </motion.div>
          </div>
        </form>
      </div>

      {/* Render status indicator */}
      {renderStatusIndicator()}
    </div>
  );
} 