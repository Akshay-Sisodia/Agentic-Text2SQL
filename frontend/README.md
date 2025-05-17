# Text2SQL Frontend

This is the React-based frontend for the Agentic Text2SQL application. It provides a modern and responsive user interface for interacting with the Text2SQL API.

## Development Setup

1. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

3. Open [http://localhost:5173](http://localhost:5173) in your browser.

## API Integration

The frontend communicates with the Text2SQL API running on the backend. By default, it assumes the API is running at `http://localhost:8000/api/v1` during development.

The main API endpoints used are:

- `/api/v1/process` - Process natural language queries to SQL
- `/api/v1/database/connect` - Connect to a database
- `/api/v1/database/status` - Check database connection status 
- `/api/v1/schema` - Get database schema information
- `/api/v1/agent/info` - Get information about available agents
- `/api/v1/execute-custom-sql` - Execute custom SQL queries

## Building for Production

To build the frontend for production:

```bash
npm run build
# or
pnpm build
```

The build output will be in the `dist` directory, ready to be served by a static file server or integrated with the backend.

## Integration with Backend

For production deployment, the frontend works with relative API paths (`/api/v1/...`), making it easy to serve both frontend and backend from the same domain. 

The Vite development server is configured to proxy API requests to the backend server during development, allowing you to work on both parts independently.
