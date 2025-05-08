# Agentic Text-to-SQL

A production-level Agentic Text-to-SQL system using PydanticAI. This application allows users to query databases using natural language, which is then automatically translated into SQL queries.

## Features

- **Natural Language to SQL**: Convert natural language questions into SQL queries
- **Multi-stage Processing Pipeline**:
  - Intent Classification: Determine the query intent and extract entities
  - SQL Generation: Generate accurate SQL based on the intent
  - Query Execution: Execute the SQL query against the database
  - Explanation Generation: Provide human-friendly explanations of the query
- **Conversation Memory**: Maintain context across multiple queries
- **Automatic Schema Discovery**: Analyze database structure automatically
- **Multiple Explanation Styles**: Technical, simplified, educational, or brief explanations

## Project Structure

```
Agentic-Text2SQL/
├── app/
│   ├── agents/             # PydanticAI agents
│   │   ├── intent_agent.py     # Intent classification
│   │   ├── sql_agent.py        # SQL generation
│   │   └── explanation_agent.py# Query explanation
│   ├── api/                # API endpoints
│   │   └── api.py          # FastAPI routes
│   ├── core/               # Core functionality
│   │   ├── config.py       # Application settings
│   │   └── database.py     # Database connection
│   ├── schemas/            # Pydantic schemas
│   │   ├── user_query.py   # User query schemas
│   │   ├── sql.py          # SQL generation schemas
│   │   └── response.py     # Response schemas
│   ├── utils/              # Utility functions
│   │   ├── db_utils.py     # Database utilities
│   │   └── sample_db.py    # Sample database creation
│   └── tests/              # Test cases
├── main.py                 # Application entry point
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # Project documentation
```

## Installation

### Prerequisites

- Python 3.11 or higher
- Access to an LLM API provider (Groq, OpenAI, etc.)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/agentic-text2sql.git
   cd agentic-text2sql
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Set up environment variables in a `.env` file:
   ```
   DEBUG=true
   LOG_LEVEL=INFO
   DB_TYPE=sqlite
   DB_NAME=text2sql.db
   LLM_PROVIDER=groq
   LLM_MODEL=llama-3.1-8b
   LLM_API_KEY=your-api-key
   ```

## Usage

### Starting the Server

```bash
python main.py
```

The server will start on http://localhost:8000 by default.

### API Endpoints

- `POST /api/v1/process`: Process a natural language query
  ```json
  {
    "query": "Find all orders from John Smith",
    "explanation_type": "SIMPLIFIED",
    "execute_query": true
  }
  ```

- `GET /api/v1/conversations/{conversation_id}`: Get conversation history

- `GET /api/v1/schema`: Get database schema information

### API Documentation

Access the interactive API documentation at:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Sample Queries

The system comes with a pre-configured sample database with customers, products, orders, and order items. Here are some sample queries you can try:

- "Show me all customers"
- "What are the top 5 most expensive products?"
- "How many orders did John Smith place?"
- "What is the total amount of all orders?"
- "List all products in the Electronics category"
- "Show me orders with a total amount greater than $500"

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [PydanticAI](https://ai.pydantic.dev/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
