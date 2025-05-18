# Agentic-Text2SQL

A production-level agentic system for converting natural language to SQL using LLMs and PydanticAI.

## Features

- Convert natural language queries to optimized SQL for multiple database types
- Support for PostgreSQL, MySQL, Microsoft SQL Server, Oracle, and SQLite
- Web UI for easy interaction with the system
- CLI for command-line interaction
- Enhanced Intent Classification with PydanticAI
- Multi-database support with SQLAlchemy
- Comes with a sample database for immediate use without configuration
- Smart entity detection with Levenshtein distance for fuzzy matching table and column names
- Comprehensive database optimization tools for all supported database types
- Persistent conversation storage with SQLite backend
- Comprehensive SQL validation with performance optimization suggestions

## Recent Updates

- Added database optimization for SQL Server and Oracle with database-specific tuning
- Enhanced index suggestion logic using database-specific mechanisms (DMVs for SQL Server, etc.)
- Added database optimization command in CLI for analyzing and improving database performance
- Implemented Levenshtein distance algorithm for better column and table name suggestions
- Added persistent conversation storage with database backend
- Enhanced SQLite schema extraction using true async operations
- Added detection of missing indices and optimization suggestions in SQL validation
- Improved entity name disambiguation with similarity matching
- Added built-in sample database for out-of-the-box functionality
- Added enhanced Intent Classification Agent using PydanticAI with improved schema awareness
- Implemented error handling and retry logic for robust agent behavior
- Added API support for selecting between standard and enhanced agents
- Fixed column name display issues in query results

## Installation

1. Clone the repository:
```bash
git clone https://github.com/akshay-sisodia/Agentic-Text2SQL.git
cd Agentic-Text2SQL
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables (optional - the system works with the sample database without configuration):
```
cp .env.example .env
```
Then edit `.env` to add your database credentials and LLM API keys.

## Usage

### Web UI

Run the FastAPI server:
```bash
uvicorn main:app --reload
```

Then visit `http://localhost:8000` in your browser.

### CLI

```bash
# Run a natural language query
python cli.py query "Show me all products with price greater than $50"

# Run in interactive mode
python cli.py query --interactive

# Execute raw SQL
python cli.py run-sql "SELECT * FROM products LIMIT 10"

# Display database schema
python cli.py schema

# Optimize database performance
python cli.py optimize --suggest-indices
```

### Database Optimization

The system includes built-in database optimization tools:

```bash
# Basic optimization (runs database-specific analysis)
python cli.py optimize

# Suggest potential indices for performance improvement
python cli.py optimize --suggest-indices
```

## Sample Database

The system includes a sample SQLite database with a retail store schema. This database contains:

- Products and categories
- Users and their addresses
- Orders and order items
- Payments and reviews

You can start using the system immediately with this sample database without any configuration. The sample database automatically connects when you start the application. You can also switch to your own database at any time through the UI or API.

To regenerate the sample database:
```bash
python generate_sample_db.py
```

## Configuration

See `.env.example` for available configuration options.

## Contributing

 See the [GitHub Issues](https://github.com/akshay-sisodia/Agentic-Text2SQL/issues) for project status and roadmap.

## License

MIT
