import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  SelectChangeEvent,
  Snackbar,
  Alert,
  TextField,
  Typography,
  Tooltip,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import SettingsIcon from '@mui/icons-material/Settings';
import StorageIcon from '@mui/icons-material/Storage';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import FileOpenIcon from '@mui/icons-material/FileOpen';

import { apiService } from '../../../services/apiService';
import type { DatabaseType, DatabaseConnectionRequest, DatabaseConfig } from '../../../types/api';

const DATABASE_TYPES: DatabaseType[] = [
  {
    id: 'sqlite',
    name: 'SQLite',
    description: 'Lightweight file-based database',
    requiresAuth: false,
    requiresHost: false,
  },
  {
    id: 'postgresql',
    name: 'PostgreSQL',
    description: 'Advanced open-source relational database',
    defaultPort: 5432,
    requiresAuth: true,
    requiresHost: true,
  },
  {
    id: 'mysql',
    name: 'MySQL',
    description: 'Popular open-source relational database',
    defaultPort: 3306,
    requiresAuth: true,
    requiresHost: true,
  },
  {
    id: 'mssql',
    name: 'Microsoft SQL Server',
    description: 'Enterprise-level relational database by Microsoft',
    defaultPort: 1433,
    requiresAuth: true,
    requiresHost: true,
  },
  {
    id: 'oracle',
    name: 'Oracle',
    description: 'Enterprise database management system',
    defaultPort: 1521,
    requiresAuth: true,
    requiresHost: true,
  },
];

interface DatabaseConnectionModalProps {
  open: boolean;
  onClose: () => void;
}

const DatabaseConnectionModal: React.FC<DatabaseConnectionModalProps> = ({ open, onClose }) => {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('md'));
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // State for form fields
  const [dbType, setDbType] = useState<string>('sqlite');
  const [dbName, setDbName] = useState<string>('text2sql');
  const [dbHost, setDbHost] = useState<string>('localhost');
  const [dbPort, setDbPort] = useState<string>('');
  const [dbUser, setDbUser] = useState<string>('');
  const [dbPassword, setDbPassword] = useState<string>('');
  const [connectionUrl, setConnectionUrl] = useState<string>('');
  const [useConnectionUrl, setUseConnectionUrl] = useState<boolean>(false);
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // State for API operations
  const [loading, setLoading] = useState<boolean>(false);
  const [testLoading, setTestLoading] = useState<boolean>(false);
  const [testSuccess, setTestSuccess] = useState<boolean | null>(null);
  const [testMessage, setTestMessage] = useState<string>('');
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });
  
  // Get current database type
  const selectedDbType = DATABASE_TYPES.find(type => type.id === dbType) || DATABASE_TYPES[0];
  
  // Load current database configuration and check connection status
  useEffect(() => {
    if (open) {
      loadDatabaseConfig();
      checkConnectionStatus();
    }
  }, [open]);
  
  // Handle database type change
  const handleDbTypeChange = (event: SelectChangeEvent) => {
    const newType = event.target.value;
    setDbType(newType);
    
    // Set default port based on database type
    const dbTypeInfo = DATABASE_TYPES.find(type => type.id === newType);
    if (dbTypeInfo && dbTypeInfo.defaultPort) {
      setDbPort(dbTypeInfo.defaultPort.toString());
    } else {
      setDbPort('');
    }
  };
  
  // Load current database configuration
  const loadDatabaseConfig = async () => {
    try {
      setLoading(true);
      const config = await apiService.getDatabaseConfig();
      
      setDbType(config.db_type || 'sqlite');
      setDbName(config.db_name || 'text2sql');
      setDbHost(config.db_host || 'localhost');
      setDbPort(config.db_port ? config.db_port.toString() : '');
      setDbUser(config.db_user || '');
      setConnectionUrl(config.connection_url || '');
      
      // Detect if using connection URL
      setUseConnectionUrl(!!config.connection_url);
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to load database configuration:', error);
      setLoading(false);
      
      // Show error notification
      setNotification({
        open: true,
        message: 'Failed to load database configuration',
        severity: 'error',
      });
    }
  };
  
  // Check current database connection status
  const checkConnectionStatus = async () => {
    try {
      const status = await apiService.getDatabaseStatus();
      
      if (status.connected) {
        setTestSuccess(true);
        setTestMessage(status.message);
        
        // Show success notification
        setNotification({
          open: true,
          message: `Connected to ${status.dialect || 'database'}`,
          severity: 'success',
        });
      }
    } catch (error) {
      console.error('Failed to check connection status:', error);
      // Don't show error notification for this, it's just a status check
    }
  };
  
  // Connect to database
  const connectToDatabase = async () => {
    try {
      setTestLoading(true);
      setTestSuccess(null);
      setTestMessage('');
      
      const connectionDetails: DatabaseConnectionRequest = {
        db_type: dbType,
        db_name: dbName,
      };
      
      if (useConnectionUrl) {
        connectionDetails.database_url = connectionUrl;
      } else {
        if (selectedDbType.requiresHost) {
          connectionDetails.db_host = dbHost;
          connectionDetails.db_port = dbPort ? parseInt(dbPort, 10) : undefined;
        }
        
        if (selectedDbType.requiresAuth) {
          connectionDetails.db_user = dbUser;
          connectionDetails.db_password = dbPassword;
        }
      }
      
      // Use the connectToDatabase method (which establishes a persistent connection)
      const result = await apiService.connectToDatabase(connectionDetails);
      
      setTestSuccess(result.success);
      setTestMessage(result.message);
      setTestLoading(false);
      
      if (result.success) {
        setNotification({
          open: true,
          message: 'Connection successful! The connection has been stored for future requests.',
          severity: 'success',
        });
      } else {
        setNotification({
          open: true,
          message: `Connection failed: ${result.message}`,
          severity: 'error',
        });
      }
    } catch (error) {
      console.error('Failed to connect to database:', error);
      setTestLoading(false);
      setTestSuccess(false);
      setTestMessage('An error occurred while connecting to the database');
      
      setNotification({
        open: true,
        message: 'Failed to connect to database',
        severity: 'error',
      });
    }
  };
  
  // Close notification
  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };
  
  // Handle file selection
  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    
    // Show guidance for SQLite connection URL
    setNotification({
      open: true,
      message: `Selected file: ${file.name}. Please verify the connection URL is correct.`,
      severity: 'info',
    });
    
    // Suggest a connection URL format but don't automatically set it
    if (file.name.endsWith('.db') || file.name.endsWith('.sqlite') || file.name.endsWith('.sqlite3')) {
      // Example: C:/path/to/your/file.db
      setConnectionUrl(`sqlite:///C:/path/to/${file.name}`);
      
      // Show more detailed instructions after a short delay
      setTimeout(() => {
        setNotification({
          open: true,
          message: `For SQLite, use format: sqlite:///C:/full/path/to/${file.name} (with forward slashes)`,
          severity: 'info',
        });
      }, 2000);
    }
    
    setUseConnectionUrl(true);
  };
  
  // Handle click on file selector button
  const handleFileSelectClick = () => {
    fileInputRef.current?.click();
  };
  
  // Handle file input change
  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };
  
  // Handle drag events
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (dbType === 'sqlite') {
      setIsDragging(true);
    }
  }, [dbType]);
  
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);
  
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (dbType === 'sqlite') {
      setIsDragging(true);
    }
  }, [dbType]);
  
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (dbType !== 'sqlite') return;
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.db') || file.name.endsWith('.sqlite') || file.name.endsWith('.sqlite3')) {
        handleFileSelect(file);
      } else {
        setNotification({
          open: true,
          message: 'Please select a valid SQLite database file (.db, .sqlite, or .sqlite3)',
          severity: 'error',
        });
      }
    }
  }, [dbType]);
  
  return (
    <>
      <Dialog
        fullScreen={fullScreen}
        open={open}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        PaperProps={{
          className: 'glass-card',
          sx: {
            backgroundImage: 'linear-gradient(to bottom, rgba(17, 25, 40, 0.75), rgba(17, 25, 40, 0.9))',
          }
        }}
      >
        <DialogTitle sx={{ m: 0, p: 2, borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <StorageIcon sx={{ mr: 1 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Database Connection
            </Typography>
            <IconButton
              aria-label="close"
              onClick={onClose}
              sx={{ color: theme.palette.grey[500] }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 0.5 }}>
            Connect to a database to use with Text-to-SQL. The connection will be stored for all queries.
          </Typography>
        </DialogTitle>
        
        <DialogContent 
          dividers 
          sx={{ borderColor: 'rgba(255, 255, 255, 0.1)', pt: 3 }}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box>
              <FormControlLabel
                control={
                  <Checkbox 
                    checked={useConnectionUrl} 
                    onChange={(e) => setUseConnectionUrl(e.target.checked)}
                  />
                }
                label="Use connection URL"
                sx={{ mb: 2 }}
              />
              
              {useConnectionUrl ? (
                <>
                  <TextField
                    fullWidth
                    label="Connection URL"
                    value={connectionUrl}
                    onChange={(e) => setConnectionUrl(e.target.value)}
                    placeholder="e.g. postgresql://user:password@localhost:5432/database"
                    margin="normal"
                    variant="outlined"
                    sx={{
                      backgroundColor: 'rgba(17, 25, 40, 0.4)',
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: 'rgba(255, 255, 255, 0.1)',
                        },
                      },
                    }}
                  />
                  
                  {dbType === 'sqlite' && (
                    <Box 
                      sx={{ 
                        mt: 2, 
                        p: 3,
                        border: '2px dashed',
                        borderColor: isDragging ? 'primary.main' : 'rgba(255, 255, 255, 0.2)',
                        borderRadius: 2,
                        backgroundColor: isDragging ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                        textAlign: 'center',
                        transition: 'all 0.2s ease',
                        cursor: 'pointer',
                      }}
                      onClick={handleFileSelectClick}
                    >
                      <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileInputChange}
                        accept=".db,.sqlite,.sqlite3"
                        style={{ display: 'none' }}
                      />
                      
                      <UploadFileIcon 
                        sx={{ 
                          fontSize: 48, 
                          color: isDragging ? 'primary.main' : 'text.secondary',
                          mb: 1
                        }} 
                      />
                      
                      <Typography variant="body1" gutterBottom>
                        {isDragging 
                          ? 'Drop SQLite database file here' 
                          : 'Drag & drop your SQLite database file here'}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        or
                      </Typography>
                      
                      <Button
                        variant="outlined"
                        startIcon={<FileOpenIcon />}
                        size="small"
                      >
                        Browse Files
                      </Button>
                      
                      {selectedFile && (
                        <Box sx={{ mt: 2, p: 1, backgroundColor: 'rgba(0, 0, 0, 0.1)', borderRadius: 1 }}>
                          <Typography variant="body2" color="primary">
                            Selected: {selectedFile.name}
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  )}
                </>
              ) : (
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth margin="normal" variant="outlined" sx={{
                      backgroundColor: 'rgba(17, 25, 40, 0.4)',
                      '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                          borderColor: 'rgba(255, 255, 255, 0.1)',
                        },
                      },
                    }}>
                      <InputLabel>Database Type</InputLabel>
                      <Select
                        value={dbType}
                        onChange={handleDbTypeChange}
                        label="Database Type"
                      >
                        {DATABASE_TYPES.map(type => (
                          <MenuItem key={type.id} value={type.id}>
                            {type.name}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                      {selectedDbType.description}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Database Name"
                      value={dbName}
                      onChange={(e) => setDbName(e.target.value)}
                      margin="normal"
                      variant="outlined"
                      sx={{
                        backgroundColor: 'rgba(17, 25, 40, 0.4)',
                        '& .MuiOutlinedInput-root': {
                          '& fieldset': {
                            borderColor: 'rgba(255, 255, 255, 0.1)',
                          },
                        },
                      }}
                    />
                  </Grid>
                  
                  {selectedDbType.requiresHost && (
                    <>
                      <Grid item xs={12} md={8}>
                        <TextField
                          fullWidth
                          label="Host"
                          value={dbHost}
                          onChange={(e) => setDbHost(e.target.value)}
                          margin="normal"
                          variant="outlined"
                          placeholder="localhost"
                          sx={{
                            backgroundColor: 'rgba(17, 25, 40, 0.4)',
                            '& .MuiOutlinedInput-root': {
                              '& fieldset': {
                                borderColor: 'rgba(255, 255, 255, 0.1)',
                              },
                            },
                          }}
                        />
                      </Grid>
                      
                      <Grid item xs={12} md={4}>
                        <TextField
                          fullWidth
                          label="Port"
                          value={dbPort}
                          onChange={(e) => setDbPort(e.target.value)}
                          margin="normal"
                          variant="outlined"
                          placeholder={selectedDbType.defaultPort?.toString()}
                          sx={{
                            backgroundColor: 'rgba(17, 25, 40, 0.4)',
                            '& .MuiOutlinedInput-root': {
                              '& fieldset': {
                                borderColor: 'rgba(255, 255, 255, 0.1)',
                              },
                            },
                          }}
                        />
                      </Grid>
                    </>
                  )}
                  
                  {selectedDbType.requiresAuth && (
                    <>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Username"
                          value={dbUser}
                          onChange={(e) => setDbUser(e.target.value)}
                          margin="normal"
                          variant="outlined"
                          sx={{
                            backgroundColor: 'rgba(17, 25, 40, 0.4)',
                            '& .MuiOutlinedInput-root': {
                              '& fieldset': {
                                borderColor: 'rgba(255, 255, 255, 0.1)',
                              },
                            },
                          }}
                        />
                      </Grid>
                      
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Password"
                          type={showPassword ? 'text' : 'password'}
                          value={dbPassword}
                          onChange={(e) => setDbPassword(e.target.value)}
                          margin="normal"
                          variant="outlined"
                          sx={{
                            backgroundColor: 'rgba(17, 25, 40, 0.4)',
                            '& .MuiOutlinedInput-root': {
                              '& fieldset': {
                                borderColor: 'rgba(255, 255, 255, 0.1)',
                              },
                            },
                          }}
                          InputProps={{
                            endAdornment: (
                              <InputAdornment position="end">
                                <IconButton
                                  onClick={() => setShowPassword(!showPassword)}
                                  edge="end"
                                >
                                  {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                </IconButton>
                              </InputAdornment>
                            ),
                          }}
                        />
                      </Grid>
                    </>
                  )}
                </Grid>
              )}
              
              {testSuccess !== null && (
                <Paper elevation={0} sx={{ 
                  p: 2, 
                  mt: 3, 
                  backgroundColor: testSuccess 
                    ? 'rgba(16, 185, 129, 0.1)' 
                    : 'rgba(239, 68, 68, 0.1)',
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                }}>
                  {testSuccess ? (
                    <CheckCircleOutlineIcon color="success" sx={{ mr: 1 }} />
                  ) : (
                    <ErrorOutlineIcon color="error" sx={{ mr: 1 }} />
                  )}
                  <Typography variant="body2">
                    {testMessage}
                  </Typography>
                </Paper>
              )}
              
              <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <HelpOutlineIcon fontSize="small" sx={{ mr: 1 }} />
                  <strong>Need help?</strong>
                </Box>
                Refer to the <a href="#" style={{ color: theme.palette.primary.main }}>Database Guide</a> for information on configuring different database types.
              </Typography>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions sx={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', p: 2 }}>
          <Button 
            onClick={connectToDatabase} 
            color="primary" 
            variant="outlined"
            disabled={testLoading || loading}
            startIcon={testLoading ? <CircularProgress size={20} /> : <SettingsIcon />}
          >
            Connect to Database
          </Button>
          <Button 
            onClick={onClose} 
            color="primary" 
            variant="contained"
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
      
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity} 
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default DatabaseConnectionModal; 