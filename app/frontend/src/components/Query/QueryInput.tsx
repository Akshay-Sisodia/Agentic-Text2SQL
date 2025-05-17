import React, { useEffect, useState } from 'react';
import { ExplanationType, AgentType } from '../../types/api';
import type { AgentInfoResponse } from '../../types/api';
import { apiService } from '../../services/apiService';
import '../../styles/query-form.css';

// Import Shadcn components
import { Button } from "../ui/button";
import { 
  PlayArrowIcon, 
  CloseIcon, 
  HelpOutlineIcon 
} from "../ui/icons";

interface QueryInputProps {
  query: string;
  setQuery: (query: string) => void;
  explanationType: ExplanationType;
  setExplanationType: (type: ExplanationType) => void;
  executeQuery: boolean;
  setExecuteQuery: (execute: boolean) => void;
  agentType: AgentType;
  setAgentType: (type: AgentType) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

const QueryInput: React.FC<QueryInputProps> = ({
  query,
  setQuery,
  explanationType,
  setExplanationType,
  executeQuery,
  setExecuteQuery,
  agentType,
  setAgentType,
  onSubmit,
  isLoading,
}) => {
  const [agentInfo, setAgentInfo] = useState<AgentInfoResponse | null>(null);

  useEffect(() => {
    // Fetch agent info when component mounts
    const fetchAgentInfo = async () => {
      try {
        const data = await apiService.getAgentInfo();
        setAgentInfo(data);
        setAgentType(AgentType.ENHANCED);
      } catch (error) {
        console.error('Failed to fetch agent info:', error);
      }
    };
    
    fetchAgentInfo();
  }, [setAgentType]);

  const handleExplanationTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setExplanationType(event.target.value as ExplanationType);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() === '') return;
    onSubmit();
  };

  const handleClear = () => {
    setQuery('');
  };

  return (
    <div className="query-container">
      <div className="query-header">
        <h2>Turn Your Questions Into SQL</h2>
        <p>Ask questions about your database in plain English and get SQL queries and visualized results instantly.</p>
      </div>
      
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <textarea
            className="query-textarea"
            placeholder="Ask a question about your database (e.g., Show me all customers from New York)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={3}
          />
          {query && (
            <button 
              type="button" 
              onClick={handleClear} 
              className="absolute right-3 top-3 text-white-70 hover-text-white"
              aria-label="Clear query"
            >
              <CloseIcon className="h-5 w-5" />
            </button>
          )}
        </div>

        <div className="query-options">
          <div className="query-option">
            <div className="query-switch">
              <div 
                className={`query-switch-track ${executeQuery ? 'active' : ''}`}
                onClick={() => setExecuteQuery(!executeQuery)}
              >
                <div className="query-switch-thumb" />
              </div>
              <span className="query-switch-label">Execute query</span>
              <div className="tooltip ml-2">
                <HelpOutlineIcon className="h-4 w-4 text-white-60" />
                <span className="tooltip-text">When enabled, the generated SQL will be executed against the database</span>
              </div>
            </div>
          </div>

          <div className="query-option">
            <div className="query-select-wrapper">
              <select
                className="query-select"
                value={explanationType}
                onChange={handleExplanationTypeChange}
              >
                <option value={ExplanationType.SIMPLIFIED}>Simplified explanation</option>
                <option value={ExplanationType.TECHNICAL}>Technical explanation</option>
                <option value={ExplanationType.EDUCATIONAL}>Educational explanation</option>
                <option value={ExplanationType.BRIEF}>Brief explanation</option>
              </select>
              <div className="tooltip absolute right-0 top-0 transform translate-y-negative-50" style={{ right: "-25px", top: "50%" }}>
                <HelpOutlineIcon className="h-4 w-4 text-white-60" />
                <span className="tooltip-text">Choose the level of detail for the explanation of the generated SQL</span>
              </div>
            </div>
          </div>
        </div>
        
        <Button
          type="submit"
          className="query-button"
          disabled={!query.trim() || isLoading}
        >
          <PlayArrowIcon className="h-5 w-5 mr-2" />
          {isLoading ? 'Processing...' : 'Generate SQL'}
        </Button>
      </form>
    </div>
  );
};

export default QueryInput; 