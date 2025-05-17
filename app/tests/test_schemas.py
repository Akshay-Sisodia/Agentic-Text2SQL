import pytest
from pydantic import ValidationError

from app.schemas.user_query import UserQuery, IntentOutput, Entity
from app.schemas.sql import DatabaseInfo, TableInfo, ColumnInfo, SQLGenerationOutput
from app.schemas.response import QueryResult, UserExplanation, ExplanationType


class TestUserQuerySchemas:
    def test_user_query_creation(self):
        """Test creating a valid UserQuery object."""
        query = UserQuery(text="Show me all customers from New York")
        assert query.text == "Show me all customers from New York"
    
    def test_empty_user_query_invalid(self):
        """Test that an empty user query is invalid."""
        with pytest.raises(ValidationError):
            UserQuery(text="")
    
    def test_entity_creation(self):
        """Test creating a valid Entity object."""
        entity = Entity(name="customers", type="TABLE")
        assert entity.name == "customers"
        assert entity.type == "TABLE"
    
    def test_user_intent_creation(self):
        """Test creating a valid IntentOutput object."""
        entities = [Entity(name="customers", type="TABLE"), Entity(name="NY", type="VALUE")]
        intent = IntentOutput(
            query_type="SELECT",
            entities=entities,
            is_ambiguous=False
        )
        assert intent.query_type == "SELECT"
        assert len(intent.entities) == 2
        assert intent.is_ambiguous is False


class TestSQLSchemas:
    def test_column_info_creation(self):
        """Test creating a valid ColumnInfo object."""
        column = ColumnInfo(
            name="id",
            data_type="INTEGER",
            primary_key=True,
            nullable=False
        )
        assert column.name == "id"
        assert column.data_type == "INTEGER"
        assert column.primary_key is True
        assert column.nullable is False
    
    def test_table_info_creation(self):
        """Test creating a valid TableInfo object."""
        columns = [
            ColumnInfo(name="id", data_type="INTEGER", primary_key=True, nullable=False),
            ColumnInfo(name="name", data_type="TEXT", nullable=False)
        ]
        table = TableInfo(
            name="customers",
            description="Customer information",
            columns=columns
        )
        assert table.name == "customers"
        assert len(table.columns) == 2
    
    def test_database_info_creation(self):
        """Test creating a valid DatabaseInfo object."""
        table = TableInfo(
            name="customers",
            description="Customer information",
            columns=[
                ColumnInfo(name="id", data_type="INTEGER", primary_key=True, nullable=False),
                ColumnInfo(name="name", data_type="TEXT", nullable=False)
            ]
        )
        db_schema = DatabaseInfo(name="test_db", tables=[table])
        assert db_schema.name == "test_db"
        assert len(db_schema.tables) == 1
    
    def test_sql_generation_output(self):
        """Test creating a valid SQLGenerationOutput object."""
        output = SQLGenerationOutput(
            sql="SELECT * FROM customers",
            confidence=0.95
        )
        assert output.sql == "SELECT * FROM customers"
        assert output.confidence == 0.95
        assert isinstance(output.warnings, list)


class TestResponseSchemas:
    def test_query_result_creation(self):
        """Test creating a valid QueryResult object."""
        result = QueryResult(
            status="SUCCESS",
            rows=[{"id": 1, "name": "John"}],
            row_count=1,
            column_names=["id", "name"]
        )
        assert result.status == "SUCCESS"
        assert result.row_count == 1
        assert len(result.rows) == 1
    
    def test_explanation_creation(self):
        """Test creating a valid UserExplanation object."""
        explanation = UserExplanation(
            text="This query returns all customers.",
            type=ExplanationType.SIMPLIFIED
        )
        assert explanation.text == "This query returns all customers."
        assert explanation.type == ExplanationType.SIMPLIFIED 