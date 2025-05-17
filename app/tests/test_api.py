import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.schemas.user_query import IntentOutput, Entity
from app.schemas.sql import SQLGenerationOutput
from app.schemas.response import UserExplanation, ExplanationType, QueryResult
from app.core.config import settings


class TestAPIEndpoints:
    @patch('app.api.api.get_schema_info')
    @patch('app.api.api.classify_intent')
    @patch('app.api.api.generate_sql')
    @patch('app.api.api.execute_generated_sql')
    @patch('app.api.api.generate_explanation')
    def test_process_query_endpoint(self, mock_generate_explanation, mock_execute_sql, 
                                     mock_generate_sql, mock_classify_intent, 
                                     mock_get_schema_info, test_client, sample_db_schema, 
                                     mock_sql_output, mock_query_result):
        """Test the main query processing endpoint."""
        # Configure mocks
        mock_get_schema_info.return_value = sample_db_schema
        
        # Mock intent classification
        mock_intent = IntentOutput(
            query_type="SELECT",
            entities=[Entity(name="customers", type="TABLE"), Entity(name="NY", type="VALUE")],
            is_ambiguous=False
        )
        mock_classify_intent.return_value = mock_intent
        
        # Mock SQL generation
        mock_generate_sql.return_value = mock_sql_output
        
        # Mock SQL execution
        mock_execute_sql.return_value = mock_query_result
        
        # Mock explanation generation
        mock_explanation = UserExplanation(
            text="This query returns all customers from New York state.",
            type=ExplanationType.SIMPLIFIED
        )
        mock_generate_explanation.return_value = mock_explanation
        
        # Test the endpoint
        response = test_client.post(
            f"{settings.API_PREFIX}/process",
            json={
                "query": "Show me all customers from New York",
                "explanation_type": "SIMPLIFIED",
                "execute_query": True
            }
        )
        
        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert result["user_response"]["sql_generation"]["sql"] == mock_sql_output.sql
        assert result["user_response"]["intent"]["query_type"] == "SELECT"
        assert result["user_response"]["query_result"]["row_count"] == 2
        assert result["user_response"]["explanation"]["text"] == mock_explanation.text
        assert "conversation_id" in result
        
        # Verify that all functions were called
        mock_get_schema_info.assert_called_once()
        mock_classify_intent.assert_called_once()
        mock_generate_sql.assert_called_once()
        mock_execute_sql.assert_called_once()
        mock_generate_explanation.assert_called_once()
    
    @patch('app.api.api.get_schema_info')
    def test_get_schema_endpoint(self, mock_get_schema_info, test_client, sample_db_schema):
        """Test the schema retrieval endpoint."""
        # Configure mock
        mock_get_schema_info.return_value = sample_db_schema
        
        # Test the endpoint
        response = test_client.get(f"{settings.API_PREFIX}/schema")
        
        # Assertions
        assert response.status_code == 200
        schema = response.json()
        assert schema["name"] == "test_db"
        assert len(schema["tables"]) == 2
        
        # Check table names
        table_names = [table["name"] for table in schema["tables"]]
        assert "customers" in table_names
        assert "orders" in table_names
        
        # Verify that get_schema_info was called
        mock_get_schema_info.assert_called_once()
    
    @patch('app.api.api.get_schema_info')
    @patch('app.api.api.classify_intent')
    @patch('app.api.api.generate_sql') 
    @patch('app.api.api.execute_generated_sql')
    @patch('app.api.api.generate_explanation')
    def test_conversation_endpoint(self, mock_generate_explanation, mock_execute_sql,
                                   mock_generate_sql, mock_classify_intent,
                                   mock_get_schema_info, test_client, sample_db_schema,
                                   mock_sql_output, mock_query_result):
        """Test the conversation history endpoint."""
        # Configure mocks
        mock_get_schema_info.return_value = sample_db_schema
        
        # Mock intent classification
        mock_intent = IntentOutput(
            query_type="SELECT",
            entities=[Entity(name="customers", type="TABLE")],
            is_ambiguous=False
        )
        mock_classify_intent.return_value = mock_intent
        
        # Mock SQL generation
        mock_generate_sql.return_value = mock_sql_output
        
        # Mock SQL execution
        mock_execute_sql.return_value = mock_query_result
        
        # Mock explanation generation
        mock_explanation = UserExplanation(
            text="This query returns all customers.",
            type=ExplanationType.SIMPLIFIED
        )
        mock_generate_explanation.return_value = mock_explanation
        
        # Step 1: Create a conversation
        response = test_client.post(
            f"{settings.API_PREFIX}/process",
            json={
                "query": "Show me all customers",
                "explanation_type": "SIMPLIFIED",
                "execute_query": True
            }
        )
        
        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]
        
        # Step 2: Get the conversation history
        # Mock the conversation getter to return a predefined conversation history
        with patch('app.api.api.conversations', {
            conversation_id: [
                {
                    "role": "user",
                    "content": "Show me all customers",
                    "timestamp": "2023-06-01T12:00:00"
                },
                {
                    "role": "assistant",
                    "content": "This query returns all customers.",
                    "sql": "SELECT * FROM customers",
                    "timestamp": "2023-06-01T12:00:01"
                }
            ]
        }):
            response = test_client.get(f"{settings.API_PREFIX}/conversations/{conversation_id}")
            
            # Assertions
            assert response.status_code == 200
            history = response.json()
            assert isinstance(history, list)
            assert len(history) == 2
            assert history[0]["role"] == "user"
            assert history[1]["role"] == "assistant"
        
    def test_nonexistent_conversation(self, test_client):
        """Test retrieving a nonexistent conversation."""
        response = test_client.get(f"{settings.API_PREFIX}/conversations/nonexistent-id")
        
        # Should return 404
        assert response.status_code == 404 