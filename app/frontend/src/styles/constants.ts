/**
 * Design system constants
 */

export const colors = {
  // Primary colors
  primary: {
    main: '#6366f1',
    light: '#818cf8',
    dark: '#4f46e5',
  },
  
  // Secondary colors
  secondary: {
    main: '#10b981', 
    light: '#34d399',
    dark: '#059669',
  },
  
  // Purple colors
  purple: {
    main: '#8b5cf6',
    light: '#a78bfa',
    dark: '#7c3aed',
  },
  
  // Background colors
  background: {
    dark: '#111827',
    darker: '#0a101f',
    card: 'rgba(17, 25, 40, 0.75)',
  },
  
  // Text colors
  text: {
    primary: '#f9fafb',
    secondary: '#d1d5db',
    muted: '#9ca3af',
  },
};

export const gradients = {
  primaryPurple: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
  hoverPurple: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)',
  primaryToWhite: 'linear-gradient(135deg, #f9fafb 0%, #6366f1 100%)',
  purpleToWhite: 'linear-gradient(135deg, #f9fafb 0%, #8b5cf6 100%)',
  cardOverlay: 'linear-gradient(to top, rgba(17, 25, 40, 0.9) 0%, rgba(17, 25, 40, 0) 100%)',
  backgroundGradient: 'linear-gradient(180deg, rgba(17, 25, 40, 0) 0%, rgba(99, 102, 241, 0.06) 100%)',
  purpleBackgroundGradient: 'linear-gradient(180deg, rgba(17, 25, 40, 0) 0%, rgba(139, 92, 246, 0.06) 100%)',
};

export const glassMorphism = {
  background: 'rgba(17, 25, 40, 0.75)',
  border: '1px solid rgba(255, 255, 255, 0.125)',
  backdropFilter: 'blur(16px)',
}; 