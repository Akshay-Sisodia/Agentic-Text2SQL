import React from 'react';
import { Box, Paper, Typography } from '@mui/material';
import type { UserExplanation } from '../../../types/api';

interface ExplanationPanelProps {
  explanation: UserExplanation;
}

const ExplanationPanel: React.FC<ExplanationPanelProps> = ({ explanation }) => {
  // Add defensive checks for undefined explanation
  if (!explanation) {
    return (
      <Paper 
        elevation={0} 
        className="glass-card" 
        sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6">Explanation</Typography>
          <Typography variant="body1" color="text.secondary">
            No explanation available
          </Typography>
        </Box>
      </Paper>
    );
  }

  // Ensure explanation_type has valid value - check both possible fields
  const explanationType = explanation.explanation_type || explanation.type || '';
  const explanationTypeDisplay = explanationType && typeof explanationType === 'string' 
    ? explanationType.charAt(0).toUpperCase() + explanationType.slice(1) 
    : 'Unknown';

  return (
    <Paper 
      elevation={0} 
      className="glass-card" 
      sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      <Box 
        sx={{ 
          p: 2, 
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }}
      >
        <Typography variant="h6">Explanation</Typography>
        <Typography variant="caption" color="text.secondary">
          {explanationTypeDisplay} explanation
        </Typography>
      </Box>

      <Box sx={{ p: 2, flexGrow: 1, overflow: 'auto' }}>
        <Typography variant="body1" component="div" sx={{ whiteSpace: 'pre-wrap' }}>
          {explanation.text || 'No explanation text available'}
        </Typography>

        {/* Show referenced concepts if available */}
        {explanation.referenced_concepts && explanation.referenced_concepts.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ color: 'primary.light' }}>
              Referenced SQL Concepts:
            </Typography>
            <ul style={{ paddingLeft: '1.5rem', margin: 0 }}>
              {explanation.referenced_concepts.map((concept, index) => (
                <li key={index}>
                  <Typography variant="body2" color="text.secondary">
                    {concept}
                  </Typography>
                </li>
              ))}
            </ul>
          </Box>
        )}

        {explanation.additional_notes && explanation.additional_notes.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ color: 'primary.light' }}>
              Additional Notes:
            </Typography>
            <ul style={{ paddingLeft: '1.5rem', margin: 0 }}>
              {explanation.additional_notes.map((note, index) => (
                <li key={index}>
                  <Typography variant="body2" color="text.secondary">
                    {note}
                  </Typography>
                </li>
              ))}
            </ul>
          </Box>
        )}

        {explanation.sql_breakdown && Object.keys(explanation.sql_breakdown).length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom sx={{ color: 'primary.light' }}>
              SQL Breakdown:
            </Typography>
            <Box sx={{ pl: 2, borderLeft: '2px solid rgba(99, 102, 241, 0.3)' }}>
              {Object.entries(explanation.sql_breakdown).map(([part, explanation], index) => (
                <Box key={index} sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {part}:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {explanation}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default ExplanationPanel; 