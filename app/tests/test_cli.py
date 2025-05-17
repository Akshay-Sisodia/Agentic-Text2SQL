import pytest
from unittest.mock import patch, MagicMock, call, ANY

from app.schemas.user_query import IntentOutput, Entity
from app.schemas.sql import SQLGenerationOutput
from app.schemas.response import UserExplanation as Explanation, ExplanationType, QueryResult


class TestCLI:
    """Tests for the CLI interface. These tests verify the flow of user interaction with the text-to-SQL CLI."""
    @patch('builtins.input')
    @patch('builtins.print')
    @patch('app.utils.db_utils.get_schema_info')
    @patch('app.agents.intent_agent.classify_intent')
    @patch('app.agents.sql_agent.generate_sql')
    @patch('app.utils.db_utils.execute_generated_sql')
    @patch('app.agents.explanation_agent.generate_explanation')
    def test_cli_flow(self, mock_generate_explanation, mock_execute_sql,
                      mock_generate_sql, mock_classify_intent,
                      mock_get_schema_info, mock_print, mock_input, sample_db_schema):
        """Test the main CLI flow with a complete query -> SQL -> explanation cycle."""
        # Configure mocks for user input - simulate one query then exit
        mock_input.side_effect = [
            "Show me all customers from New York",  # User query
            "y",  # Execute SQL? 
            "2",  # Explanation style
            "exit"  # End session
        ]
        
        # Mock schema retrieval
        mock_get_schema_info.return_value = sample_db_schema
        
        # Mock intent classification
        mock_intent = IntentOutput(
            query_type="SELECT",
            entities=[Entity(name="customers", type="TABLE"), Entity(name="NY", type="VALUE")],
            is_ambiguous=False
        )
        mock_classify_intent.return_value = mock_intent
        
        # Mock SQL generation
        mock_sql = SQLGenerationOutput(
            sql="SELECT * FROM customers WHERE state = 'NY'",
            explanation="This query returns all customers from New York."
        )
        mock_generate_sql.return_value = mock_sql
        
        # Mock SQL execution
        mock_result = QueryResult(
            status="SUCCESS",
            rows=[
                {"id": 1, "name": "John Doe", "email": "john@example.com", "city": "New York", "state": "NY"},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "city": "Buffalo", "state": "NY"}
            ],
            row_count=2,
            column_names=["id", "name", "email", "city", "state"],
            error_message=None
        )
        mock_execute_sql.return_value = mock_result
        
        # Mock explanation generation
        mock_explanation = Explanation(
            text="This query returns all customers from New York state.",
            type=ExplanationType.SIMPLIFIED
        )
        mock_generate_explanation.return_value = mock_explanation
        
        # Import and run the CLI
        import sys
        import os
        from importlib import import_module
        
        # Use a different approach to test the CLI since we patched input/print
        # Import cli_test module and call its main function
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
        cli_module = import_module('cli_test')
        
        # Run with exception handling since we're simulating exit
        try:
            cli_module.main()
        except StopIteration:
            # This happens because we mocked input with a limited sequence
            pass
        
        # Verify function calls
        mock_get_schema_info.assert_called_once()
        mock_classify_intent.assert_called_once()
        mock_generate_sql.assert_called_once()
        mock_execute_sql.assert_called_once()
        mock_generate_explanation.assert_called_once()
        
        # Verify the explanation used the correct style
        mock_generate_explanation.assert_called_with(
            ANY, ANY, ANY, ExplanationType.SIMPLIFIED
        ) 