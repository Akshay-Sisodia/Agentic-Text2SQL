import React, { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  AppBar,
  Box,
  Button,
  Container,
  IconButton,
  Link,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  Tooltip,
  useTheme,
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import MenuIcon from '@mui/icons-material/Menu';
import SchemaIcon from '@mui/icons-material/Schema';
import HomeIcon from '@mui/icons-material/Home';
import SettingsIcon from '@mui/icons-material/Settings';
import SchemaModal from '@/components/Schema/SchemaModal';
import DatabaseConnectionModal from '@/components/Database/DatabaseConnectionModal';

const pages = [
  { name: 'Home', path: '/', icon: <HomeIcon /> },
  { name: 'Database Schema', path: '#', action: 'schema', icon: <SchemaIcon /> },
  { name: 'Connection Settings', path: '#', action: 'connection', icon: <SettingsIcon /> }
];

const Header: React.FC = () => {
  const theme = useTheme();
  const [anchorElNav, setAnchorElNav] = useState<null | HTMLElement>(null);
  const [schemaOpen, setSchemaOpen] = useState(false);
  const [connectionOpen, setConnectionOpen] = useState(false);

  const handleOpenNavMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElNav(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };

  const handleMenuClick = (action?: string) => {
    handleCloseNavMenu();
    if (action === 'schema') {
      setSchemaOpen(true);
    } else if (action === 'connection') {
      setConnectionOpen(true);
    }
  };

  return (
    <>
      <AppBar position="static" sx={{ mb: 2 }}>
        <Container maxWidth="lg">
          <Toolbar disableGutters>
            {/* Desktop logo */}
            <StorageIcon sx={{ display: { xs: 'none', md: 'flex' }, mr: 1 }} />
            <Typography
              variant="h6"
              noWrap
              component={RouterLink}
              to="/"
              sx={{
                mr: 2,
                display: { xs: 'none', md: 'flex' },
                fontWeight: 700,
                color: 'inherit',
                textDecoration: 'none',
              }}
            >
              Agentic Text-to-SQL
            </Typography>

            {/* Mobile menu */}
            <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
              <IconButton
                size="large"
                aria-label="menu"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleOpenNavMenu}
                color="inherit"
              >
                <MenuIcon />
              </IconButton>
              <Menu
                id="menu-appbar"
                anchorEl={anchorElNav}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'left',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'left',
                }}
                open={Boolean(anchorElNav)}
                onClose={handleCloseNavMenu}
                sx={{
                  display: { xs: 'block', md: 'none' },
                }}
              >
                {pages.map((page) => (
                  <MenuItem 
                    key={page.name} 
                    onClick={() => handleMenuClick(page.action)}
                  >
                    <Typography textAlign="center">
                      {React.cloneElement(page.icon, { sx: { mr: 1, fontSize: '1rem' } })}
                      {page.name}
                    </Typography>
                  </MenuItem>
                ))}
              </Menu>
            </Box>

            {/* Mobile logo */}
            <StorageIcon sx={{ display: { xs: 'flex', md: 'none' }, mr: 1 }} />
            <Typography
              variant="h6"
              noWrap
              component={RouterLink}
              to="/"
              sx={{
                mr: 2,
                display: { xs: 'flex', md: 'none' },
                flexGrow: 1,
                fontWeight: 700,
                color: 'inherit',
                textDecoration: 'none',
              }}
            >
              Agentic Text-to-SQL
            </Typography>

            {/* Desktop menu */}
            <Box sx={{ 
              flexGrow: 1, 
              display: { xs: 'none', md: 'flex' }, 
              justifyContent: 'flex-end',
              gap: 1
            }}>
              {pages.map((page) => (
                page.action ? (
                  <Tooltip key={page.name} title={page.name}>
                    <Button
                      onClick={() => handleMenuClick(page.action)}
                      variant="text"
                      sx={{ 
                        color: 'white',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 255, 255, 0.1)'
                        },
                        borderRadius: '8px',
                        minWidth: { md: '40px', lg: 'auto' },
                        px: { md: 1.5, lg: 2 }
                      }}
                      startIcon={page.icon}
                    >
                      <Typography 
                        sx={{ 
                          display: { md: 'none', lg: 'block' } 
                        }}
                      >
                        {page.name}
                      </Typography>
                    </Button>
                  </Tooltip>
                ) : (
                  <Tooltip key={page.name} title={page.name}>
                    <Button
                      component={RouterLink}
                      to={page.path}
                      variant="text"
                      sx={{ 
                        color: 'white',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 255, 255, 0.1)'
                        },
                        borderRadius: '8px',
                        minWidth: { md: '40px', lg: 'auto' },
                        px: { md: 1.5, lg: 2 }
                      }}
                      startIcon={page.icon}
                    >
                      <Typography 
                        sx={{ 
                          display: { md: 'none', lg: 'block' } 
                        }}
                      >
                        {page.name}
                      </Typography>
                    </Button>
                  </Tooltip>
                )
              ))}
            </Box>
          </Toolbar>
        </Container>
      </AppBar>
      
      <SchemaModal open={schemaOpen} onClose={() => setSchemaOpen(false)} />
      <DatabaseConnectionModal open={connectionOpen} onClose={() => setConnectionOpen(false)} />
    </>
  );
};

export default Header; 