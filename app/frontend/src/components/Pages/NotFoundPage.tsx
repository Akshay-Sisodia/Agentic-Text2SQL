import React from 'react';
import { Box, Button, Paper, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const NotFoundPage: React.FC = () => {
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '70vh' 
      }}
      className="fade-in"
    >
      <Paper 
        elevation={0}
        className="glass-card" 
        sx={{ 
          p: 5, 
          textAlign: 'center',
          maxWidth: 600,
          backgroundImage: 'linear-gradient(to right bottom, rgba(99, 102, 241, 0.05), rgba(255, 255, 255, 0.05))'
        }}
      >
        <Typography variant="h1" component="h1" gutterBottom sx={{ fontWeight: 800 }}>
          404
        </Typography>
        <Typography variant="h4" component="h2" gutterBottom sx={{ fontWeight: 600 }}>
          Page Not Found
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4 }}>
          The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
        </Typography>
        <Button 
          variant="contained" 
          component={RouterLink} 
          to="/" 
          size="large"
        >
          Go Home
        </Button>
      </Paper>
    </Box>
  );
};

export default NotFoundPage; 