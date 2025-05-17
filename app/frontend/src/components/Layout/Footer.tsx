import React from 'react';
import { Box, Container, Typography, Link } from '@mui/material';

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        mt: 'auto',
        backgroundColor: 'rgba(17, 25, 40, 0.8)',
        backdropFilter: 'blur(10px)',
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          {'Agentic Text-to-SQL © '}
          {new Date().getFullYear()}
          {' | '}
          <Link color="inherit" href="https://github.com/" target="_blank" rel="noopener">
            GitHub
          </Link>
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer; 