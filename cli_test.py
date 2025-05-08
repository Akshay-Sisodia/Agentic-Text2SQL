import sys
import logging
from app.utils.db_utils import get_schema_info, execute_generated_sql
from app.agents.intent_agent import classify_intent
from app.agents.sql_agent import generate_sql
from app.agents.explanation_agent import generate_explanation
from app.schemas.user_query import UserQuery
from app.schemas.response import ExplanationType

logging.basicConfig(level=logging.INFO)

def main():
    print("\nAgentic Text-to-SQL CLI Test Utility\n" + "-"*40)
    schema = get_schema_info()
    print(f"Loaded schema for database: {schema.name}\n")

    while True:
        user_text = input("Enter your natural language query (or 'exit' to quit): ").strip()
        if user_text.lower() in {"exit", "quit"}:
            print("Exiting.")
            break
        if not user_text:
            continue

        user_query = UserQuery(text=user_text)
        print("\nClassifying intent...")
        intent = classify_intent(
            user_text,
            {
                t.name: {
                    "columns": {
                        c.name: {
                            "type": c.data_type,
                            "primary_key": c.primary_key,
                            "foreign_key": (
                                {"table": c.foreign_key.split(".")[0], "column": c.foreign_key.split(".")[1]}
                                if c.foreign_key and "." in c.foreign_key else None
                            ),
                            "unique": False,
                            "nullable": c.nullable
                        }
                        for c in t.columns
                    }
                }
                for t in schema.tables
            }
        )
        print(f"Intent: {intent.query_type}, Entities: {[e.name for e in intent.entities]}, Ambiguous: {intent.is_ambiguous}")
        if intent.is_ambiguous and intent.clarification_question:
            print(f"Clarification needed: {intent.clarification_question}")
            continue

        print("\nGenerating SQL...")
        sql_output = generate_sql(user_query, intent, schema)
        print(f"Generated SQL:\n{sql_output.sql}\n")
        if sql_output.explanation:
            print(f"SQL Agent Explanation: {sql_output.explanation}\n")
        if sql_output.warnings:
            print(f"Warnings: {sql_output.warnings}\n")

        execute = input("Do you want to execute this SQL on the database? [y/N]: ").strip().lower()
        query_result = None
        if execute == 'y':
            print("\nExecuting SQL...")
            query_result = execute_generated_sql(sql_output)
            if query_result.status == 'SUCCESS':
                print(f"Query executed successfully. Rows: {query_result.row_count}")
                if query_result.rows:
                    for row in query_result.rows[:5]:
                        print(row)
                    if query_result.row_count > 5:
                        print(f"... and {query_result.row_count - 5} more rows.")
            else:
                print(f"Query execution failed: {query_result.error_message}")

        print("\nExplanation styles: 1) TECHNICAL 2) SIMPLIFIED 3) EDUCATIONAL 4) BRIEF")
        style_map = {'1': ExplanationType.TECHNICAL, '2': ExplanationType.SIMPLIFIED, '3': ExplanationType.EDUCATIONAL, '4': ExplanationType.BRIEF}
        style_choice = input("Choose explanation style [1-4, default 2]: ").strip()
        explanation_type = style_map.get(style_choice, ExplanationType.SIMPLIFIED)
        print(f"\nGenerating {explanation_type.value.lower()} explanation...")
        explanation = generate_explanation(user_query, sql_output, query_result.dict() if query_result else None, explanation_type)
        print(f"\nExplanation:\n{explanation.text}\n")
        print("-"*40)

if __name__ == "__main__":
    main() 