import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add the root directory to path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.api.api import app
from app.schemas.user_query import UserQuery
from app.schemas.sql import DatabaseInfo, TableInfo, ColumnInfo, SQLGenerationOutput
from app.schemas.response import QueryResult, UserExplanation, ExplanationType


@pytest.fixture
def test_client():
    """Return a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_user_query():
    """Return a sample user query."""
    return UserQuery(text="Show me all customers from New York.")


@pytest.fixture
def sample_db_schema():
    """Return a sample database schema for testing."""
    # Create a simplified schema similar to the sample database
    customers_table = TableInfo(
        name="customers",
        description="Customer information",
        columns=[
            ColumnInfo(name="id", data_type="INTEGER", primary_key=True, nullable=False),
            ColumnInfo(name="name", data_type="TEXT", nullable=False),
            ColumnInfo(name="email", data_type="TEXT", nullable=False),
            ColumnInfo(name="city", data_type="TEXT", nullable=True),
            ColumnInfo(name="state", data_type="TEXT", nullable=True)
        ]
    )
    
    orders_table = TableInfo(
        name="orders",
        description="Customer orders",
        columns=[
            ColumnInfo(name="id", data_type="INTEGER", primary_key=True, nullable=False),
            ColumnInfo(name="customer_id", data_type="INTEGER", nullable=False, foreign_key="customers.id"),
            ColumnInfo(name="order_date", data_type="DATE", nullable=False),
            ColumnInfo(name="total_amount", data_type="DECIMAL", nullable=False)
        ]
    )
    
    return DatabaseInfo(
        name="test_db",
        tables=[customers_table, orders_table]
    )


@pytest.fixture
def mock_sql_output():
    """Return a mock SQL output."""
    return SQLGenerationOutput(
        sql="SELECT * FROM customers WHERE state = 'NY'",
        explanation="This SQL selects all customers from New York.",
        warnings=[]
    )


@pytest.fixture
def mock_query_result():
    """Return a mock query result."""
    return QueryResult(
        status="SUCCESS",
        rows=[
            {"id": 1, "name": "John Doe", "email": "john@example.com", "city": "New York", "state": "NY"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "city": "Buffalo", "state": "NY"}
        ],
        row_count=2,
        column_names=["id", "name", "email", "city", "state"],
        error_message=None
    ) 