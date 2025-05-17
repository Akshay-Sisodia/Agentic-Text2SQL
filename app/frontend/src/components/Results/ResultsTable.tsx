import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Tooltip,
  Pagination,
  Stack,
  Chip,
} from '@mui/material';
import GetAppIcon from '@mui/icons-material/GetApp';
import { QueryStatus } from '../../types/api';
import type { QueryResult } from '../../types/api';

interface ResultsTableProps {
  results: QueryResult;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ results }) => {
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Defensive check for undefined results
  if (!results) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography color="text.secondary" variant="body2">
          No query results available.
        </Typography>
      </Box>
    );
  }

  // Reset pagination when results change
  useEffect(() => {
    setPage(1);
  }, [results]);

  if (results.status === QueryStatus.ERROR) {
    return (
      <Box sx={{ p: 2, backgroundColor: 'rgba(239, 68, 68, 0.1)', borderRadius: 1 }}>
        <Typography color="error" variant="body2">
          Error executing query: {results.error_message || 'Unknown error'}
        </Typography>
      </Box>
    );
  }

  if (!results.rows || results.rows.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          {results.execution_time && (
            <Chip 
              label={`Query executed in ${results.execution_time} sec`} 
              size="small"
              color="primary"
              variant="outlined" 
            />
          )}
        </Box>
        <Typography color="text.secondary" variant="body2">
          Query executed successfully, but no results were returned.
        </Typography>
        {results.affected_rows && (
          <Typography variant="body2" sx={{ mt: 1 }}>
            {results.affected_rows} {results.affected_rows === 1 ? 'row' : 'rows'} affected.
          </Typography>
        )}
      </Box>
    );
  }

  // Use either columns or column_names, whichever is available
  // If neither is available, extract column names from the first row
  let columnsList: string[] = [];
  if (results.columns && results.columns.length > 0) {
    columnsList = results.columns;
  } else if (results.column_names && results.column_names.length > 0) {
    columnsList = results.column_names;
  } else if (results.rows.length > 0) {
    // Extract column names from the first row as a fallback
    columnsList = Object.keys(results.rows[0]);
  }

  if (columnsList.length === 0) {
    return (
      <Box sx={{ p: 2, textAlign: 'center' }}>
        <Typography color="text.secondary" variant="body2">
          Results contain data but no column definitions.
        </Typography>
      </Box>
    );
  }

  // Pagination
  const startIndex = (page - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const displayedRows = results.rows.slice(startIndex, endIndex);
  const totalPages = Math.ceil(results.rows.length / rowsPerPage);

  const handleChangePage = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const downloadCSV = () => {
    // Create CSV content
    const headers = columnsList.join(',');
    const rows = results.rows.map(row => {
      return columnsList.map(col => {
        const value = row[col];
        // Handle strings with commas by wrapping in quotes
        if (typeof value === 'string' && value.includes(',')) {
          return `"${value}"`;
        }
        return value === null ? '' : value;
      }).join(',');
    }).join('\n');
    
    const csvContent = `${headers}\n${rows}`;
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    // Create a download link and trigger it
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'query_results.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, alignItems: 'center' }}>
        <Box>
          <Chip 
            label={`${results.rows.length} results`} 
            size="small" 
            color="primary" 
            variant="outlined" 
          />
          {results.execution_time && (
            <Chip 
              label={`${results.execution_time} sec`} 
              size="small" 
              sx={{ ml: 1 }} 
              variant="outlined" 
            />
          )}
        </Box>
        <Tooltip title="Download as CSV">
          <IconButton onClick={downloadCSV} size="small">
            <GetAppIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <div className="table-container">
        <table className="glassmorphic-table">
          <thead>
            <tr>
              {columnsList.map((column, index) => (
                <th key={index}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayedRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {columnsList.map((column, colIndex) => (
                  <td key={colIndex}>
                    {row[column] === null ? (
                      <Typography variant="body2" color="text.disabled" sx={{ fontStyle: 'italic' }}>
                        NULL
                      </Typography>
                    ) : (
                      String(row[column])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <Stack direction="row" spacing={2} sx={{ mt: 2, justifyContent: 'center' }}>
          <Pagination 
            count={totalPages} 
            page={page} 
            onChange={handleChangePage} 
            color="primary" 
            size="small"
            siblingCount={1}
          />
        </Stack>
      )}
    </Box>
  );
};

export default ResultsTable; 