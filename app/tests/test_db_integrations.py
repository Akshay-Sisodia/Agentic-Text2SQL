import pytest
from unittest.mock import patch, MagicMock

from app.core.config import settings


class TestDatabaseIntegrations:
    @patch('main.create_sample_database')
    @patch('main.create_sample_postgres_database')
    @patch('main.create_sample_mysql_database')
    @patch('main.create_sample_mssql_database')
    @patch('main.create_sample_oracle_database')
    @patch('main.settings')
    def test_db_selection_sqlite(self, mock_settings, mock_oracle, mock_mssql,
                                mock_mysql, mock_postgres, mock_sqlite):
        """Test SQLite database initialization."""
        # Configure mock to use SQLite
        mock_settings.DB_TYPE = "sqlite"
        
        # Import and call lifespan
        from main import lifespan
        app_mock = MagicMock()
        async def run_lifespan():
            async with lifespan(app_mock):
                pass
        
        # Run the async context manager
        import asyncio
        asyncio.run(run_lifespan())
        
        # Verify only SQLite initialize function was called
        mock_sqlite.assert_called_once()
        mock_postgres.assert_not_called()
        mock_mysql.assert_not_called()
        mock_mssql.assert_not_called()
        mock_oracle.assert_not_called()
    
    @patch('main.create_sample_database')
    @patch('main.create_sample_postgres_database')
    @patch('main.create_sample_mysql_database')
    @patch('main.create_sample_mssql_database')
    @patch('main.create_sample_oracle_database')
    @patch('main.settings')
    def test_db_selection_postgres(self, mock_settings, mock_oracle, mock_mssql,
                                   mock_mysql, mock_postgres, mock_sqlite):
        """Test PostgreSQL database initialization."""
        # Configure mock to use PostgreSQL
        mock_settings.DB_TYPE = "postgresql"
        
        # Import and call lifespan
        from main import lifespan
        app_mock = MagicMock()
        async def run_lifespan():
            async with lifespan(app_mock):
                pass
        
        # Run the async context manager
        import asyncio
        asyncio.run(run_lifespan())
        
        # Verify only PostgreSQL initialize function was called
        mock_sqlite.assert_not_called()
        mock_postgres.assert_called_once()
        mock_mysql.assert_not_called()
        mock_mssql.assert_not_called()
        mock_oracle.assert_not_called()
    
    @patch('main.create_sample_database')
    @patch('main.create_sample_postgres_database')
    @patch('main.create_sample_mysql_database')
    @patch('main.create_sample_mssql_database')
    @patch('main.create_sample_oracle_database')
    @patch('main.settings')
    def test_db_selection_mysql(self, mock_settings, mock_oracle, mock_mssql,
                               mock_mysql, mock_postgres, mock_sqlite):
        """Test MySQL database initialization."""
        # Configure mock to use MySQL
        mock_settings.DB_TYPE = "mysql"
        
        # Import and call lifespan
        from main import lifespan
        app_mock = MagicMock()
        async def run_lifespan():
            async with lifespan(app_mock):
                pass
        
        # Run the async context manager
        import asyncio
        asyncio.run(run_lifespan())
        
        # Verify only MySQL initialize function was called
        mock_sqlite.assert_not_called()
        mock_postgres.assert_not_called()
        mock_mysql.assert_called_once()
        mock_mssql.assert_not_called()
        mock_oracle.assert_not_called()
    
    @patch('main.create_sample_database')
    @patch('main.create_sample_postgres_database')
    @patch('main.create_sample_mysql_database')
    @patch('main.create_sample_mssql_database')
    @patch('main.create_sample_oracle_database')
    @patch('main.settings')
    def test_db_unsupported_type(self, mock_settings, mock_oracle, mock_mssql,
                                mock_mysql, mock_postgres, mock_sqlite):
        """Test handling of unsupported database type."""
        # Configure mock to use unsupported type
        mock_settings.DB_TYPE = "unsupported"
        
        # Import and call lifespan
        from main import lifespan
        app_mock = MagicMock()
        async def run_lifespan():
            async with lifespan(app_mock):
                pass
        
        # Run the async context manager
        import asyncio
        asyncio.run(run_lifespan())
        
        # Verify no database initialize functions were called
        mock_sqlite.assert_not_called()
        mock_postgres.assert_not_called()
        mock_mysql.assert_not_called()
        mock_mssql.assert_not_called()
        mock_oracle.assert_not_called() 