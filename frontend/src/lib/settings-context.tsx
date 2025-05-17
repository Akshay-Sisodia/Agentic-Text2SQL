import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

// Define settings interface for type safety
export interface UserSettings {
  preferredExplanationType: 'SIMPLIFIED' | 'TECHNICAL' | 'EDUCATIONAL' | 'BRIEF';
  useEnhancedAgent: boolean;
  darkMode: boolean;
  resultPreview: boolean;
}

// Default settings
export const defaultSettings: UserSettings = {
  preferredExplanationType: 'SIMPLIFIED',
  useEnhancedAgent: true,
  darkMode: true,
  resultPreview: true
};

interface SettingsContextType {
  settings: UserSettings;
  updateSettings: (newSettings: Partial<UserSettings>) => void;
  saveSettings: () => void;
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<UserSettings>(defaultSettings);

  useEffect(() => {
    // Load settings from localStorage on component mount
    loadSettings();
  }, []);

  const loadSettings = () => {
    try {
      const savedSettings = localStorage.getItem('userSettings');
      if (savedSettings) {
        setSettings(JSON.parse(savedSettings));
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const updateSettings = (newSettings: Partial<UserSettings>) => {
    setSettings(prev => ({
      ...prev,
      ...newSettings
    }));
  };

  const saveSettings = () => {
    try {
      localStorage.setItem('userSettings', JSON.stringify(settings));
    } catch (error) {
      console.error('Error saving settings:', error);
      throw error;
    }
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings, saveSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
} 