import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { 
        find: '@', 
        replacement: path.resolve(__dirname, './src') 
      },
      // Add explicit resolution for lib paths
      { 
        find: '@/lib/settings-context', 
        replacement: path.resolve(__dirname, './src/lib/settings-context.tsx') 
      },
      { 
        find: '@/lib/utils', 
        replacement: path.resolve(__dirname, './src/lib/utils.ts') 
      },
      { 
        find: '@/lib/api', 
        replacement: path.resolve(__dirname, './src/lib/api.ts') 
      },
      { 
        find: '@/lib/hooks', 
        replacement: path.resolve(__dirname, './src/lib/hooks.ts') 
      }
    ],
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json']
  },
  server: {
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
