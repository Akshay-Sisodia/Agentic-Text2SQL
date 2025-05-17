import pytest
from unittest.mock import patch, MagicMock

from app.agents.intent_agent import classify_intent, intent_agent
from app.agents.sql_agent import generate_sql, sql_agent
from app.agents.explanation_agent import generate_explanation, explanation_agent
from app.schemas.user_query import UserQuery, IntentOutput, Entity
from app.schemas.sql import SQLGenerationOutput
from app.schemas.response import UserExplanation as Explanation, ExplanationType, QueryResult


class TestIntentAgent:
    @patch('app.agents.intent_agent.intent_agent.run_sync')
    def test_classify_intent_basic(self, mock_run_sync):
        """Test basic intent classification functionality."""
        # Setup mock Agent response
        mock_result = MagicMock()
        mock_result.data = IntentOutput(
            query_type="SELECT",
            entities=[Entity(name="customers", type="TABLE"), Entity(name="NY", type="VALUE")],
            is_ambiguous=False
        )
        mock_run_sync.return_value = mock_result
        
        # Test intent classification
        schema_dict = {
            "customers": {
                "columns": {
                    "id": {"type": "INTEGER", "primary_key": True, "foreign_key": None, "unique": False, "nullable": False},
                    "name": {"type": "TEXT", "primary_key": False, "foreign_key": None, "unique": False, "nullable": False},
                    "state": {"type": "TEXT", "primary_key": False, "foreign_key": None, "unique": False, "nullable": True}
                }
            }
        }
        
        result = classify_intent("Show me all customers from New York", schema_dict)
        
        # Assertions
        assert result.query_type == "SELECT"
        assert len(result.entities) == 2
        assert result.is_ambiguous is False
        
        # Verify Agent was called with expected arguments
        mock_run_sync.assert_called_once()
        # Check the first positional argument is the user query
        args, _ = mock_run_sync.call_args
        assert args[0] == "Show me all customers from New York"


class TestSQLAgent:
    @patch('app.agents.sql_agent.sql_agent.run_sync')
    def test_generate_sql_basic(self, mock_run_sync, sample_db_schema):
        """Test basic SQL generation functionality."""
        # Setup mock Agent response
        mock_result = MagicMock()
        mock_result.data = SQLGenerationOutput(
            sql="SELECT * FROM customers WHERE state = 'NY'",
            explanation="This query returns all customers from New York.",
            warnings=[]
        )
        mock_run_sync.return_value = mock_result
        
        # Test data
        user_query = UserQuery(text="Show me all customers from New York")
        intent = IntentOutput(
            query_type="SELECT",
            entities=[Entity(name="customers", type="TABLE"), Entity(name="NY", type="VALUE")],
            is_ambiguous=False
        )
        db_schema = sample_db_schema
        
        # Generate SQL
        result = generate_sql(user_query.text, intent, db_schema)
        
        # Assertions
        assert result.sql == "SELECT * FROM customers WHERE state = 'NY'"
        assert "New York" in result.explanation
        
        # Verify Agent was called
        mock_run_sync.assert_called_once()


class TestExplanationAgent:
    @patch('app.agents.explanation_agent.explanation_agent.run_sync')
    def test_generate_explanation_basic(self, mock_run_sync):
        """Test basic explanation generation functionality."""
        # Setup mock Agent response
        mock_result = MagicMock()
        mock_result.data = Explanation(
            text="This query finds all customers who are from New York state by filtering the customers table.",
            type=ExplanationType.SIMPLIFIED
        )
        mock_run_sync.return_value = mock_result
        
        # Test data
        user_query = UserQuery(text="Show me all customers from New York")
        sql_output = SQLGenerationOutput(
            sql="SELECT * FROM customers WHERE state = 'NY'",
            explanation="This SQL selects all customers from New York."
        )
        query_result = {
            "status": "SUCCESS",
            "rows": [
                {"id": 1, "name": "John Doe", "state": "NY"},
                {"id": 2, "name": "Jane Smith", "state": "NY"}
            ],
            "row_count": 2,
            "columns": ["id", "name", "state"]
        }
        
        # Generate explanation
        result = generate_explanation(user_query, sql_output, query_result, ExplanationType.SIMPLIFIED)
        
        # Assertions
        assert "New York" in result.text
        assert result.type == ExplanationType.SIMPLIFIED
        
        # Verify Agent was called
        mock_run_sync.assert_called_once() 