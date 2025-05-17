import pytest
from unittest.mock import patch, MagicMock
import sqlite3

from app.utils.db_utils import get_schema_info, execute_generated_sql
from app.schemas.sql import SQLGenerationOutput, TableInfo, ColumnInfo


class TestDatabaseUtils:
    @patch('app.utils.db_utils.get_table_info')
    @patch('app.utils.db_utils.get_engine')
    def test_get_schema_info_sqlite(self, mock_get_engine, mock_get_table_info):
        """Test schema extraction for SQLite database using a simpler approach."""
        # Mock the engine
        mock_engine = MagicMock()
        mock_engine.name = 'sqlite'
        mock_engine.url.database = 'test_db'
        mock_engine.driver = 'sqlite3'
        mock_get_engine.return_value = mock_engine
        
        # Set up a mock connection
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        
        # Mock table results
        mock_tables_result = MagicMock()
        mock_tables_result.__iter__.return_value = [('customers',), ('orders',)]
        mock_connection.execute.return_value = mock_tables_result
        
        # Create mock table info objects
        customers_table = TableInfo(
            name="customers",
            columns=[
                ColumnInfo(name="id", data_type="INTEGER", primary_key=True, nullable=False),
                ColumnInfo(name="name", data_type="TEXT", nullable=False),
                ColumnInfo(name="email", data_type="TEXT", nullable=False),
                ColumnInfo(name="city", data_type="TEXT", nullable=True),
                ColumnInfo(name="state", data_type="TEXT", nullable=True)
            ],
            row_count=10
        )
        
        orders_table = TableInfo(
            name="orders",
            columns=[
                ColumnInfo(name="id", data_type="INTEGER", primary_key=True, nullable=False),
                ColumnInfo(name="customer_id", data_type="INTEGER", nullable=False, foreign_key="customers.id"),
                ColumnInfo(name="order_date", data_type="DATE", nullable=False),
                ColumnInfo(name="total_amount", data_type="DECIMAL", nullable=False)
            ],
            row_count=25
        )
        
        # Set up the get_table_info mock to return our pre-created table objects
        mock_get_table_info.side_effect = [customers_table, orders_table]
        
        # Call the function
        schema = get_schema_info()
        
        # Check how many times execute was called
        print(f"Execute called {mock_connection.execute.call_count} times")
        
        # Assertions
        assert schema.name == 'test_db'
        assert len(schema.tables) == 2
        
        # Check table names
        table_names = [table.name for table in schema.tables]
        assert 'customers' in table_names
        assert 'orders' in table_names
        
        # Check customer columns
        customers_table = next(table for table in schema.tables if table.name == 'customers')
        assert len(customers_table.columns) == 5
        assert customers_table.columns[0].name == 'id'
        assert customers_table.columns[0].primary_key is True
        
        # Check orders foreign key
        orders_table = next(table for table in schema.tables if table.name == 'orders')
        customer_id_column = next(col for col in orders_table.columns if col.name == 'customer_id')
        assert customer_id_column.foreign_key == 'customers.id'
    
    @patch('app.utils.db_utils.execute_query')
    def test_execute_generated_sql_success(self, mock_execute_query):
        """Test successful SQL execution."""
        # Mock the execute_query result
        mock_result = MagicMock()
        mock_result.status = 'SUCCESS'
        mock_result.rows = [
            {"id": 1, "name": "John Doe", "state": "NY"},
            {"id": 2, "name": "Jane Smith", "state": "NY"}
        ]
        mock_result.row_count = 2
        mock_result.column_names = ['id', 'name', 'state']
        mock_result.error_message = None
        mock_execute_query.return_value = mock_result
        
        # Create SQL output
        sql_output = SQLGenerationOutput(sql="SELECT * FROM customers WHERE state = 'NY'")
        
        # Execute the SQL
        result = execute_generated_sql(sql_output)
        
        # Assertions
        assert result.status == 'SUCCESS'
        assert result.row_count == 2
        assert len(result.rows) == 2
        assert result.rows[0]['name'] == 'John Doe'
        assert result.column_names == ['id', 'name', 'state']
        assert result.error_message is None
        
        # Verify execute_query was called with the correct SQL
        mock_execute_query.assert_called_once_with("SELECT * FROM customers WHERE state = 'NY'")
    
    @patch('app.utils.db_utils.execute_query')
    def test_execute_generated_sql_error(self, mock_execute_query):
        """Test SQL execution with an error."""
        # Mock execute_query to return an error
        mock_result = MagicMock()
        mock_result.status = 'ERROR'
        mock_result.error_message = "no such column: non_existent_column"
        mock_result.rows = []
        mock_execute_query.return_value = mock_result
        
        # Create SQL output with invalid SQL
        sql_output = SQLGenerationOutput(sql="SELECT non_existent_column FROM customers")
        
        # Execute the SQL
        result = execute_generated_sql(sql_output)
        
        # Assertions
        assert result.status == 'ERROR'
        assert result.rows == []
        assert "no such column" in result.error_message
        
        # Verify execute_query was called with the correct SQL
        mock_execute_query.assert_called_once_with("SELECT non_existent_column FROM customers") 