import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Grid,
  Divider,
  IconButton,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CloseIcon from '@mui/icons-material/Close';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import KeyIcon from '@mui/icons-material/Key';
import LinkIcon from '@mui/icons-material/Link';

import { apiService } from '../../../services/apiService';
import type { DatabaseInfo, TableInfo, ColumnInfo } from '../../../types/api';
import { useQuery } from 'react-query';

interface SchemaModalProps {
  open: boolean;
  onClose: () => void;
}

const SchemaModal: React.FC<SchemaModalProps> = ({ open, onClose }) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  
  const { data: schema, isLoading, error } = useQuery<DatabaseInfo>(
    'database-schema',
    () => apiService.getDatabaseSchema(),
    {
      enabled: open,
      staleTime: 60 * 60 * 1000, // 1 hour
    }
  );
  
  return (
    <Dialog
      fullScreen={fullScreen}
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        className: 'glass-card',
        sx: {
          overflowY: 'visible',
          backgroundImage: 'linear-gradient(to right bottom, rgba(17, 25, 40, 0.75), rgba(17, 25, 40, 0.85))',
        }
      }}
    >
      <DialogTitle sx={{ m: 0, p: 2, borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <Typography variant="h6" component="div" sx={{ display: 'flex', alignItems: 'center' }}>
          Database Schema
        </Typography>
        <IconButton
          aria-label="close"
          onClick={onClose}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: 'text.secondary',
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      
      <DialogContent dividers sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Typography color="error" sx={{ p: 2 }}>
            Error loading database schema. Please try again later.
          </Typography>
        ) : schema ? (
          <Box>
            <Typography variant="h6" gutterBottom>
              {schema.name}
            </Typography>
            {schema.description && (
              <Typography variant="body2" color="text.secondary" paragraph>
                {schema.description}
              </Typography>
            )}
            
            <Box sx={{ mt: 3 }}>
              {schema.tables.map((table) => (
                <Accordion 
                  key={table.name} 
                  disableGutters 
                  elevation={0}
                  sx={{ 
                    mb: 2, 
                    backgroundColor: 'rgba(17, 25, 40, 0.5)',
                    backgroundImage: 'linear-gradient(to right, rgba(99, 102, 241, 0.1), rgba(17, 25, 40, 0.5))',
                    '&:before': {
                      display: 'none',
                    },
                  }}
                >
                  <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    sx={{ 
                      borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <Typography variant="subtitle1" fontWeight={600}>
                      {table.name}
                    </Typography>
                    {table.description && (
                      <IconButton 
                        size="small" 
                        sx={{ ml: 1, color: 'text.secondary' }}
                        title={table.description}
                      >
                        <InfoOutlinedIcon fontSize="small" />
                      </IconButton>
                    )}
                  </AccordionSummary>
                  <AccordionDetails>
                    <TableColumns table={table} />
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          </Box>
        ) : (
          <Typography sx={{ p: 2 }}>No schema information available.</Typography>
        )}
      </DialogContent>
      
      <DialogActions sx={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', p: 2 }}>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

interface TableColumnsProps {
  table: TableInfo;
}

const TableColumns: React.FC<TableColumnsProps> = ({ table }) => {
  return (
    <Box sx={{ width: '100%', overflow: 'auto' }}>
      <table className="glassmorphic-table">
        <thead>
          <tr>
            <th>Column</th>
            <th>Type</th>
            <th>Description</th>
            <th>Attributes</th>
          </tr>
        </thead>
        <tbody>
          {table.columns.map((column) => (
            <tr key={column.name}>
              <td style={{ fontWeight: column.primary_key ? 600 : 400 }}>
                {column.name}
                {column.primary_key && (
                  <KeyIcon 
                    fontSize="small" 
                    sx={{ ml: 1, verticalAlign: 'middle', color: theme => theme.palette.warning.main }}
                  />
                )}
              </td>
              <td>{column.data_type}</td>
              <td>{column.description || '-'}</td>
              <td>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {column.primary_key && (
                    <Chip 
                      label="Primary Key" 
                      size="small" 
                      color="warning"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }}
                    />
                  )}
                  {column.foreign_key && (
                    <Chip 
                      label={`FK: ${column.foreign_key}`} 
                      size="small" 
                      color="info"
                      variant="outlined"
                      icon={<LinkIcon />}
                      sx={{ fontSize: '0.7rem' }}
                    />
                  )}
                  {!column.nullable && (
                    <Chip 
                      label="NOT NULL" 
                      size="small" 
                      color="secondary"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }}
                    />
                  )}
                </Box>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Box>
  );
};

export default SchemaModal; 