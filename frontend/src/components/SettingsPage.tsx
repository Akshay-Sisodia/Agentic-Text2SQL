import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings, Check, PenSquare, Info, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getAgentInfo } from '@/lib/api';
import { useSettings } from '@/lib/settings-context';
import type { UserSettings } from '@/lib/settings-context';

export function SettingsPage() {
  const { settings, updateSettings, saveSettings } = useSettings();
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  
  const [agentInfo, setAgentInfo] = useState({
    enhanced_available: false,
    current_agent_type: 'base',
    message: 'Loading agent information...'
  });

  useEffect(() => {
    // Fetch agent info when component mounts
    fetchAgentInfo();
  }, []);

  const handleSettingChange = (setting: keyof UserSettings, value: UserSettings[typeof setting]) => {
    updateSettings({ [setting]: value });
    
    // Clear any previous save status message
    if (saveStatus) {
      setSaveStatus(null);
    }
  };

  const fetchAgentInfo = async () => {
    try {
      const info = await getAgentInfo();
      setAgentInfo(info);
    } catch (error) {
      console.error('Error fetching agent info:', error);
     setAgentInfo(prev => ({
       ...prev,
       message: 'Unable to retrieve agent status. Please try again later.'
     }));
    }
  };
  
  const handleSaveSettings = () => {
    try {
      // Save settings using context function
      saveSettings();
      
      // Show success message
      setSaveStatus('Settings saved successfully!');
      
// Clear message after 3 seconds
 const timerId = setTimeout(() => {
   setSaveStatus(null);
 }, 3000);
 
 // This should be outside this function, in a useEffect
 // useEffect(() => {
 //   return () => {
 //     if (timerId) clearTimeout(timerId);
 //   };
 // }, [timerId]);
    } catch (error) {
      console.error('Error saving settings:', error);
      setSaveStatus('Error saving settings');
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-black/30 backdrop-blur-sm">
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto pb-8">
          <header className="mb-8">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent mb-2">
              Settings
            </h1>
            <p className="text-gray-400">
              Configure your Text-to-SQL experience and preferences.
            </p>
          </header>

          <div className="grid grid-cols-1 gap-8">
            {/* Agent Settings */}
            <motion.section 
              className="bg-white/[0.03] border border-white/10 rounded-lg p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                <Settings className="w-5 h-5 text-indigo-400" />
                Agent Settings
              </h2>
              
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-gray-300 font-medium">Explanation Type</label>
                  </div>
                  <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-labelledby="explanation-type-label">
                    {['SIMPLIFIED', 'TECHNICAL', 'EDUCATIONAL', 'BRIEF'].map((type) => (
                      <button
                        key={type}
                        className={cn(
                          "p-3 rounded-lg border flex items-center justify-center gap-2 transition-colors",
                          settings.preferredExplanationType === type
                            ? "bg-indigo-500/20 border-indigo-500/30 text-indigo-300"
                            : "border-white/10 hover:bg-white/[0.05] text-gray-300"
                        )}
                        role="radio"
                        aria-checked={settings.preferredExplanationType === type}
                        onClick={() => handleSettingChange('preferredExplanationType', type as any)}
                      >
                        {settings.preferredExplanationType === type && (
                          <Check className="w-4 h-4" />
                        )}
                        <span>{type.charAt(0) + type.slice(1).toLowerCase()}</span>
                      </button>
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    Choose how SQL explanations should be presented to you.
                  </p>
                </div>
                
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-gray-300 font-medium">Agent Model</label>
                  </div>
                  <div className="p-4 bg-white/[0.02] border border-white/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "w-3 h-3 rounded-full",
                        agentInfo.enhanced_available ? "bg-green-500" : "bg-amber-500"
                      )}></div>
                      <div>
                        <p className="text-white">
                          {agentInfo.enhanced_available ? "Enhanced Agent Available" : "Base Agent Only"}
                        </p>
                        <p className="text-sm text-gray-400">
                          {agentInfo.message}
                        </p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <button
                        className={cn(
                          "w-full flex items-center justify-center gap-2 py-2 px-4 rounded-md",
                          "bg-indigo-600/20 text-indigo-300 border border-indigo-600/30",
                          "hover:bg-indigo-600/30 transition-colors"
                        )}
                        onClick={fetchAgentInfo}
                      >
                        <Info className="w-4 h-4" />
                        <span>Check Agent Status</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </motion.section>
            
            {/* User Interface Settings */}
            <motion.section 
              className="bg-white/[0.03] border border-white/10 rounded-lg p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                <PenSquare className="w-5 h-5 text-indigo-400" />
                User Interface
              </h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-300 font-medium">Dark Mode</p>
                    <p className="text-xs text-gray-500">
                      Use dark theme for the interface
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer" 
                      checked={settings.darkMode}
                      onChange={(e) => handleSettingChange('darkMode', e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-white/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                  </label>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-300 font-medium">Result Preview</p>
                    <p className="text-xs text-gray-500">
                      Preview query results while typing
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      className="sr-only peer" 
                      checked={settings.resultPreview}
                      onChange={(e) => handleSettingChange('resultPreview', e.target.checked)}
                    />
                    <div className="w-11 h-6 bg-white/10 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
                  </label>
                </div>
              </div>
            </motion.section>
            
            {/* Account Settings (placeholder) */}
            <motion.section 
              className="bg-white/[0.03] border border-white/10 rounded-lg p-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                Account Settings
              </h2>
              
              <div className="text-center py-8">
                <p className="text-gray-400">
                  Account management features coming soon
                </p>
                <p className="text-sm text-gray-500 mt-2">
                  User profile, preferences, and API key management will be available in a future update.
                </p>
              </div>
            </motion.section>
            
            {/* Save button and status message */}
            <div className="flex flex-col items-end gap-2">
              {saveStatus && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    "px-4 py-2 rounded text-sm",
                    saveStatus.includes("Error") 
                      ? "bg-red-500/20 text-red-300 border border-red-500/30"
                      : "bg-green-500/20 text-green-300 border border-green-500/30"
                  )}
                >
                  {saveStatus}
                </motion.div>
              )}
              
              <motion.button 
                className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg flex items-center gap-2"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSaveSettings}
              >
                <Check className="w-4 h-4" />
                Save Settings
              </motion.button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 