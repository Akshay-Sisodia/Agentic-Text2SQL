# Database Configuration Guide

This guide explains how to configure and use different database types with the Agentic Text-to-SQL system.

## Supported Database Types

The system supports the following database types:

1. SQLite (default)
2. PostgreSQL
3. MySQL
4. Microsoft SQL Server (MSSQL)
5. Oracle

## Configuration

Database settings are configured through environment variables or in the `.env` file. Here are the available configuration options:

```
# Database settings
DATABASE_URL=                # Full connection URL (optional)
DB_TYPE=sqlite               # postgresql, mysql, sqlite, mssql, oracle
DB_NAME=text2sql             # Database name
DB_USER=                     # Database username
DB_PASSWORD=                 # Database password
DB_HOST=                     # Database host
DB_PORT=                     # Database port
```

### Using DATABASE_URL

You can provide a complete connection URL using the `DATABASE_URL` environment variable. This takes precedence over the individual settings:

```
DATABASE_URL=postgresql://user:password@localhost:5432/text2sql
```

### Database Type-Specific Configuration

#### SQLite

SQLite is the simplest to configure and is the default:

```
DB_TYPE=sqlite
DB_NAME=text2sql             # This will be the filename
```

#### PostgreSQL

```
DB_TYPE=postgresql
DB_NAME=text2sql
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

#### MySQL

```
DB_TYPE=mysql
DB_NAME=text2sql
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

#### Microsoft SQL Server

```
DB_TYPE=mssql
DB_NAME=text2sql
DB_USER=sa
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=1433
```

#### Oracle

```
DB_TYPE=oracle
DB_NAME=orcl                 # Oracle SID or service name
DB_USER=system
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=1521
```

## Required Dependencies

Different database types require different drivers. The following dependencies are needed:

- PostgreSQL: `psycopg2-binary`
- MySQL: `pymysql`
- MSSQL: `pyodbc` (requires ODBC Driver for SQL Server)
- Oracle: `cx_oracle` (requires Oracle client libraries)

All these dependencies are included in the `requirements.txt` file.

## Sample Database Creation

The system includes sample database creation scripts for all supported database types. When you start the application, it will automatically create a sample database with tables and data for testing.

The sample database includes the following tables:
- `customers`
- `products`
- `orders`
- `order_items`

## Schema Extraction

The system automatically extracts the database schema regardless of the database type. The schema information includes:

- Tables and their descriptions
- Columns with data types
- Primary and foreign keys
- Sample data values

This schema information is used by the Text-to-SQL agents to understand the database structure and generate appropriate SQL queries.

## Adding Your Own Database

To use your own database instead of the sample database:

1. Set the connection parameters in the `.env` file to connect to your existing database
2. Disable sample database creation by setting `CREATE_SAMPLE_DB=false` in your `.env` file

## Troubleshooting

### PostgreSQL Connection Issues

If you encounter connection issues with PostgreSQL, check:
- PostgreSQL service is running
- User has appropriate permissions
- Network/firewall settings allowing connections

### MySQL Connection Issues

- Ensure the MySQL service is running
- Check user permissions
- Verify that the password authentication method is compatible

### MSSQL Connection Issues

- Verify SQL Server service is running
- Check that the SQL Server Authentication mode includes SQL Server authentication if not using Windows auth
- Ensure the ODBC Driver for SQL Server is installed

### Oracle Connection Issues

- Verify Oracle database service is running
- Ensure Oracle Client libraries are installed and properly configured
- Check TNS settings if using a service name

## Advanced Settings

For more advanced connection pooling and driver-specific settings, you can modify the `get_engine()` function in `app/core/database.py`. 