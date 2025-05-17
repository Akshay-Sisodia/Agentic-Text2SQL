import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, IconButton, Tooltip, Snackbar, Alert } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CodeMirror from '@uiw/react-codemirror';
import { sql as sqlLanguage } from '@codemirror/lang-sql';
import { materialDark } from '@uiw/codemirror-theme-material';
import { apiService } from '../../services/apiService';

interface SqlResultProps {
  sql: string;
  conversationId?: string;
  onQueryResultUpdate?: (result: any) => void;
}

const SqlResult: React.FC<SqlResultProps> = ({ sql, conversationId, onQueryResultUpdate }) => {
  const [copied, setCopied] = useState(false);
  const [sqlContent, setSqlContent] = useState(sql || '');
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<{message: string, severity: 'success' | 'error' | 'info'} | null>(null);
  
  // Update internal SQL content when prop changes
  useEffect(() => {
    setSqlContent(sql || '');
  }, [sql]);

  const handleCopy = () => {
    navigator.clipboard.writeText(sqlContent);
    setCopied(true);
  };
  
  const handleSqlChange = React.useCallback((value: string) => {
    setSqlContent(value);
  }, []);
  
  const handleExecuteCustomSql = async () => {
    if (!sqlContent.trim()) return;
    
    setIsExecuting(true);
    try {
      const result = await apiService.executeCustomSql(sqlContent, conversationId);
      setExecutionResult({
        message: result.status === 'SUCCESS' 
          ? 'Query executed successfully!' 
          : `Error: ${result.error_message}`,
        severity: result.status === 'SUCCESS' ? 'success' : 'error'
      });
      
      // Pass the result up to parent component
      if (onQueryResultUpdate) {
        onQueryResultUpdate(result);
      }
    } catch (error) {
      setExecutionResult({
        message: `Error executing query: ${error instanceof Error ? error.message : 'Unknown error'}`,
        severity: 'error'
      });
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <Paper 
      elevation={0} 
      className="glass-card" 
      sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      <Box 
        sx={{ 
          p: 2, 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <Typography variant="h6">SQL Query</Typography>
        <Box>
          <Tooltip title="Run SQL Query">
            <IconButton 
              onClick={handleExecuteCustomSql} 
              size="small" 
              color="primary"
              disabled={isExecuting}
              sx={{ mr: 1 }}
            >
              <PlayArrowIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Copy SQL">
            <IconButton onClick={handleCopy} size="small">
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Box sx={{ p: 0, flexGrow: 1, overflow: 'auto', borderRadius: '0 0 8px 8px' }}>
        <CodeMirror
          value={sqlContent}
          height="200px"
          extensions={[sqlLanguage()]}
          theme={materialDark}
          editable={true}
          onChange={handleSqlChange}
          basicSetup={{
            foldGutter: true,
            dropCursor: false,
            allowMultipleSelections: false,
            indentOnInput: true,
            lineNumbers: true,
          }}
        />
      </Box>

      <Snackbar
        open={copied}
        autoHideDuration={2000}
        onClose={() => setCopied(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setCopied(false)} severity="success" sx={{ width: '100%' }}>
          SQL copied to clipboard!
        </Alert>
      </Snackbar>
      
      <Snackbar
        open={executionResult !== null}
        autoHideDuration={4000}
        onClose={() => setExecutionResult(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setExecutionResult(null)} severity={executionResult?.severity || 'info'} sx={{ width: '100%' }}>
          {executionResult?.message || ''}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default SqlResult; 