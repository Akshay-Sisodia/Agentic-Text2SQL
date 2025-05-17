#!/usr/bin/env python
"""Test the optimized intent agent with DSPy."""

import asyncio
import json
import os
from dotenv import load_dotenv

from app.agents.dspy_intent_agent import classify_intent_optimized, optimized_intent_agent


# Sample database schema for testing
SAMPLE_SCHEMA = {
    "customers": {
        "description": "Customer information",
        "columns": {
            "id": {"type": "INTEGER", "primary_key": True, "description": "Unique customer ID"},
            "name": {"type": "VARCHAR", "nullable": False, "description": "Customer full name"},
            "email": {"type": "VARCHAR", "unique": True, "description": "Customer email address"},
            "city": {"type": "VARCHAR", "description": "Customer city"},
            "state": {"type": "VARCHAR", "description": "Customer state"},
            "country": {"type": "VARCHAR", "description": "Customer country"},
            "created_at": {"type": "TIMESTAMP", "description": "When the customer was added"}
        }
    },
    "orders": {
        "description": "Customer orders",
        "columns": {
            "id": {"type": "INTEGER", "primary_key": True, "description": "Unique order ID"},
            "customer_id": {
                "type": "INTEGER", 
                "foreign_key": {"table": "customers", "column": "id"},
                "description": "Reference to customer"
            },
            "order_date": {"type": "DATE", "description": "When the order was placed"},
            "total_amount": {"type": "DECIMAL", "description": "Total order amount"},
            "status": {"type": "VARCHAR", "description": "Order status (pending, shipped, etc.)"}
        }
    },
    "products": {
        "description": "Product catalog",
        "columns": {
            "id": {"type": "INTEGER", "primary_key": True, "description": "Unique product ID"},
            "name": {"type": "VARCHAR", "nullable": False, "description": "Product name"},
            "description": {"type": "TEXT", "description": "Product description"},
            "price": {"type": "DECIMAL", "description": "Product price"},
            "category": {"type": "VARCHAR", "description": "Product category"},
            "in_stock": {"type": "BOOLEAN", "description": "Whether the product is in stock"}
        }
    },
    "order_items": {
        "description": "Items within an order",
        "columns": {
            "id": {"type": "INTEGER", "primary_key": True, "description": "Unique order item ID"},
            "order_id": {
                "type": "INTEGER", 
                "foreign_key": {"table": "orders", "column": "id"},
                "description": "Reference to order"
            },
            "product_id": {
                "type": "INTEGER", 
                "foreign_key": {"table": "products", "column": "id"},
                "description": "Reference to product"
            },
            "quantity": {"type": "INTEGER", "description": "Quantity ordered"},
            "unit_price": {"type": "DECIMAL", "description": "Price at time of order"}
        }
    }
}


# Test queries
TEST_QUERIES = [
    "Show all customers from New York",
    "List products with price greater than $50",
    "Find orders placed in the last 7 days",
    "Update the price of the 'Widget' product to $25.99",
    "How many orders did each customer place?",
    "Which customers haven't placed any orders yet?",
    "Add a new product called 'Super Widget' with a price of $99.99"
]


async def run_test():
    """Run the test on the optimized intent agent."""
    
    print("Initializing optimized intent agent...")
    # Optimize the agent (this will happen automatically on first use)
    optimized_intent_agent.optimize()
    
    print("\nTesting queries...")
    for query in TEST_QUERIES:
        print(f"\nQuery: {query}")
        
        # Process with optimized agent
        result = await classify_intent_optimized(query, SAMPLE_SCHEMA)
        
        # Print results
        print(f"Query Type: {result.query_type}")
        print(f"Is Ambiguous: {result.is_ambiguous}")
        
        if result.is_ambiguous and result.clarification_question:
            print(f"Clarification: {result.clarification_question}")
        
        print("Entities:")
        for entity in result.entities:
            print(f"  - {entity.name} ({entity.type})")
        
        print("-" * 50)


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the async test
    asyncio.run(run_test()) 