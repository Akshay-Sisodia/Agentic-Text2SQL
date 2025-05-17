"""Test for enhanced explanation agent."""

import unittest
import asyncio
from unittest.mock import AsyncMock, patch
import json
from typing import Dict, Any, List

from app.agents.pydantic_explanation_agent import generate_explanation_enhanced, enhanced_explanation_agent
from app.schemas.response import ExplanationType, QueryStatus
from app.schemas.sql import SQLGenerationOutput
from app.schemas.user_query import UserQuery, IntentType

def setup_test_data():
    """Set up test data for explanation agent"""
    
    # Create user query
    user_query = UserQuery(
        text="Show me sales by region for the last quarter",
        timestamp="2023-08-15T14:30:00",
        conversation_id="test-conversation",
        user_id="test-user"
    )
    
    # Create SQL generation output
    sql_generation = SQLGenerationOutput(
        sql="""
        SELECT r.region_name, SUM(s.amount) as total_sales
        FROM sales s
        JOIN regions r ON s.region_id = r.id
        WHERE s.sale_date >= '2023-04-01' AND s.sale_date <= '2023-06-30'
        GROUP BY r.region_name
        ORDER BY total_sales DESC
        """,
        explanation="This query retrieves sales data grouped by region for Q2 2023. It joins the sales table with the regions table to get region names, filters for the last quarter, and aggregates the sales amounts.",
        confidence_score=0.95,
        alternative_queries=[],
        query_type=IntentType.SELECT,
        tables_used=["sales", "regions"],
        columns_used=["regions.region_name", "sales.amount", "sales.region_id", "regions.id", "sales.sale_date"]
    )
    
    # Create mock query result
    mock_query_result: Dict[str, Any] = {
        "status": QueryStatus.SUCCESS,
        "rows": [
            {"region_name": "North America", "total_sales": 1250000.00},
            {"region_name": "Europe", "total_sales": 980000.00},
            {"region_name": "Asia Pacific", "total_sales": 820000.00},
            {"region_name": "Latin America", "total_sales": 450000.00},
            {"region_name": "Africa", "total_sales": 210000.00}
        ],
        "row_count": 5,
        "column_names": ["region_name", "total_sales"],
        "columns": ["region_name", "total_sales"],
        "execution_time": 0.056
    }
    
    # Create schema info
    schema_info = {
        "tables": [
            {
                "name": "sales",
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary": True},
                    {"name": "amount", "type": "DECIMAL(10,2)"},
                    {"name": "sale_date", "type": "DATE"},
                    {"name": "region_id", "type": "INTEGER"}
                ]
            },
            {
                "name": "regions",
                "columns": [
                    {"name": "id", "type": "INTEGER", "primary": True},
                    {"name": "region_name", "type": "VARCHAR(50)"},
                    {"name": "country_code", "type": "CHAR(2)"}
                ]
            }
        ]
    }
    
    return user_query, sql_generation, mock_query_result, schema_info


async def test_explanation_generation(explanation_type: ExplanationType):
    """Test explanation generation with a specific type"""
    
    user_query, sql_generation, query_result, schema_info = setup_test_data()
    
    print(f"\n===== Testing {explanation_type.value} Explanation =====\n")
    
    try:
        explanation = await generate_explanation_enhanced(
            user_query=user_query,
            sql_generation=sql_generation,
            query_result=query_result,
            explanation_type=explanation_type,
            schema_info=schema_info
        )
        
        print(f"Explanation type: {explanation.type}")
        print(f"Explanation text:\n{explanation.text}\n")
        
        if hasattr(explanation, "sql_breakdown") and explanation.sql_breakdown:
            print(f"SQL Breakdown:\n{explanation.sql_breakdown}\n")
            
        if hasattr(explanation, "query_summary") and explanation.query_summary:
            print(f"Query Summary: {explanation.query_summary}\n")
            
        print(f"Referenced Concepts: {', '.join(explanation.referenced_concepts)}")
        
        return explanation
    
    except Exception as e:
        print(f"Error generating explanation: {str(e)}")
        return None


async def test_error_handling():
    """Test error handling in the explanation agent"""
    
    user_query, sql_generation, _, _ = setup_test_data()
    
    # Create a failed query result
    failed_query_result = {
        "status": QueryStatus.ERROR,
        "error_message": "Error: column 'unknown_column' does not exist",
        "execution_time": 0.012
    }
    
    print("\n===== Testing Explanation with Failed Query =====\n")
    
    try:
        explanation = await generate_explanation_enhanced(
            user_query=user_query,
            sql_generation=sql_generation,
            query_result=failed_query_result,
            explanation_type=ExplanationType.SIMPLIFIED
        )
        
        print(f"Explanation for failed query:\n{explanation.text}\n")
        return explanation
    
    except Exception as e:
        print(f"Error handling failed query: {str(e)}")
        return None


async def run_tests():
    """Run all tests for the explanation agent"""
    
    print("\n🔍 ENHANCED EXPLANATION AGENT TESTS 🔍\n")
    print(f"Using LLM: {enhanced_explanation_agent._model_name}\n")
    
    # Test each explanation type
    for explanation_type in ExplanationType:
        await test_explanation_generation(explanation_type)
    
    # Test error handling
    await test_error_handling()


if __name__ == "__main__":
    asyncio.run(run_tests()) 