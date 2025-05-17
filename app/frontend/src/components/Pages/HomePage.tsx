import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  CircularProgress, 
  Fade,
  Grid,
  Stack,
  Divider,
  Tooltip,
  IconButton
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

import QueryInput from '../../components/Query/QueryInput';
import SqlResult from '../../components/Results/SqlResult';
import ResultsTable from '../../components/Results/ResultsTable';
import ExplanationPanel from '../../components/Results/ExplanationPanel';
import { useSqlGenerator } from '../../hooks/useSqlGenerator';
import { ExplanationType, AgentType } from '../../types/api';

const HomePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [explanationType, setExplanationType] = useState(ExplanationType.SIMPLIFIED);
  const [executeQuery, setExecuteQuery] = useState(true);
  const [agentType, setAgentType] = useState(AgentType.ENHANCED);
  
  const { 
    generateSql, 
    result, 
    isLoading, 
    error
  } = useSqlGenerator();
  
  // Track the query result in local state
  const [customQueryResult, setCustomQueryResult] = useState<any>(null);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    
    await generateSql({
      query,
      conversation_id: localStorage.getItem('conversation_id') || undefined,
      explanation_type: explanationType,
      execute_query: executeQuery,
      agent_type: agentType,
      db_type: "sqlite",  // Default to sqlite
      db_path: "sample_huge.db", // Default database path
    });
  };
  
  const handleQueryResultUpdate = (updatedResult: any) => {
    setCustomQueryResult(updatedResult);
  };
  
  return (
    <Box className="fade-in">
      <Paper 
        elevation={0} 
        className="glass-card"
        sx={{ 
          p: 3, 
          mb: 4,
          backgroundImage: 'linear-gradient(to right bottom, rgba(99, 102, 241, 0.05), rgba(16, 185, 129, 0.05))'
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Turn Your Questions Into SQL
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          Ask questions about your database in plain English and get SQL queries and visualized results instantly.
        </Typography>
        
        <QueryInput
          query={query}
          setQuery={setQuery}
          explanationType={explanationType}
          setExplanationType={setExplanationType}
          executeQuery={executeQuery}
          setExecuteQuery={setExecuteQuery}
          agentType={agentType}
          setAgentType={setAgentType}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </Paper>
      
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}
      
      {error && (
        <Paper 
          elevation={0} 
          className="glass-card"
          sx={{ p: 3, mb: 4, bgcolor: 'rgba(239, 68, 68, 0.1)' }}
        >
          <Typography color="error" variant="body1">
            Error: {error}
          </Typography>
        </Paper>
      )}
      
      {result && (
        <Fade in={!!result}>
          <Box>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              <Box sx={{ flex: '1 1 400px', minWidth: 0 }}>
                {result.user_response && result.user_response.sql_generation ? (
                  <SqlResult 
                    sql={result.user_response.sql_generation.sql} 
                    conversationId={result.conversation_id}
                    onQueryResultUpdate={handleQueryResultUpdate}
                  />
                ) : (
                  <Paper elevation={0} className="glass-card" sx={{ p: 3 }}>
                    <Typography variant="body1" color="text.secondary">
                      No SQL was generated.
                    </Typography>
                  </Paper>
                )}
              </Box>
              <Box sx={{ flex: '1 1 400px', minWidth: 0 }}>
                {result.user_response && result.user_response.explanation ? (
                  <ExplanationPanel explanation={result.user_response.explanation} />
                ) : (
                  <Paper elevation={0} className="glass-card" sx={{ p: 3 }}>
                    <Typography variant="body1" color="text.secondary">
                      No explanation available.
                    </Typography>
                  </Paper>
                )}
              </Box>
            </Box>
            
            {((result?.user_response?.query_result) || customQueryResult) && (
              <Paper 
                elevation={0} 
                className="glass-card" 
                sx={{ mt: 4, p: 3 }}
              >
                <Typography variant="h6" gutterBottom>
                  Query Results
                </Typography>
                <ResultsTable results={customQueryResult || result.user_response.query_result} />
              </Paper>
            )}
            
            {result.enhanced_agent_used && (
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  <em>Using enhanced agent (PydanticAI with DSPy)</em>
                </Typography>
              </Box>
            )}
          </Box>
        </Fade>
      )}
    </Box>
  );
};

export default HomePage; 