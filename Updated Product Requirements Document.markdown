# Product Requirements Document: Production-Level Agentic Text-to-SQL System with PydanticAI

## 1. Executive Summary

The Agentic Text-to-SQL System is a production-grade solution designed to transform natural language questions into accurate, optimized SQL queries using a multi-agent architecture powered by Large Language Models (LLMs). It empowers enterprise users—regardless of SQL expertise—to access data insights securely and efficiently. The system leverages SQLAlchemy Core for database connectivity, query execution, and schema management, LLaMa 3.1 8B via Groq for natural language understanding and generation, DSPy for continuous prompt optimization, and **PydanticAI** for defining and managing the agents. All agents are defined using Pydantic for robust data validation and agent structure. The system is built with a focus on performance, security, and scalability, ensuring robust operation in production environments.

## 2. Product Vision

To democratize data access by enabling users of all technical backgrounds to retrieve valuable insights from databases through natural language, while maintaining high performance, security, and accuracy in production environments.

## 3. Target Users

- **Business Analysts**: Need data insights without advanced SQL knowledge.
- **Data Scientists**: Accelerate data exploration workflows.
- **Product Managers**: Require quick, data-driven decisions.
- **Executives**: Seek ad-hoc reporting capabilities.
- **Customer Support**: Retrieve customer data rapidly.
- **Database Administrators**: Configure and monitor the system.
- **Data Engineers/Developers**: Use the system for rapid data access during development and testing.

## 4. Success Metrics

- **Query Accuracy**: 85%+ correct SQL translations.
- **Response Time**: <1.5s for standard queries.
- **User Satisfaction**: 95%+ positive feedback.
- **Time-to-Insight**: 30% reduction vs. manual SQL.
- **Adoption Rate**: 40% among non-technical users within 6 months.
- **Cost Efficiency**: 20% reduction in operational query costs.
- **Scalability**: Handle 1000+ queries/hour without degradation.

## 5. Agent System Architecture

The system uses a microservices architecture with each agent as a separate service, ensuring modularity, scalability, and maintainability. All agents are LLM-based, defined using **PydanticAI** for structured agent definitions, consistent agent communication patterns, and type-safe interactions. Agents communicate via RESTful APIs using FastAPI.

### 5.1 User Intent Agent (LLM-Based with PydanticAI)

**Features:**
- Natural language understanding with intent classification.
- Entity and keyword extraction.
- Contextual awareness for multi-turn conversations.
- Ambiguity detection and clarification generation.
- Query decomposition for complex requests.

**Tech Stack:**
- **PydanticAI**: Defines the agent structure and methods as Pydantic models, enabling robust agent communication and validation.
- **LLaMa 3.1 8B via Groq**: Powers the agent for intent classification, entity extraction, and context handling.
- **DSPy**: Automatic prompt optimization for improved accuracy.
- **Pydantic**: Core structure for agent inputs (e.g., `UserQuery`) and outputs (e.g., `IntentOutput`).
- **FastAPI**: API serving.

**Requirements:**
- Identify query type (e.g., SELECT, INSERT) with 95% accuracy.
- Extract entities (tables, columns, conditions) with 90% accuracy.
- Retain context across 5+ conversation turns.
- Handle 20+ common business query patterns.
- Detect ambiguities and prompt clarification within 1s.

### 5.2 Schema Mapping Agent (LLM-Based with PydanticAI)

**Features:**
- Schema ingestion and indexing using SQLAlchemy Core metadata.
- Entity-to-schema mapping with LLM-driven fuzzy matching.
- Relationship inference via foreign key detection and LLM reasoning.
- Schema synonyms dictionary and custom mappings.
- Auto-discovery of query patterns.

**Tech Stack:**
- **PydanticAI**: Defines the agent as a Pydantic model with LLM-powered methods for mapping natural language terms to schema elements.
- **SQLAlchemy Core**: Metadata reflection for schema management and relationship inference.
- **DSPy**: Optimizes mapping prompts.
- **Pydantic**: Core structure for inputs (e.g., entities) and outputs (e.g., `MappingOutput`).
- **FastAPI**: API serving.

**Requirements:**
- Index schemas with up to 200 tables and 2000 columns.
- Handle schema evolution with re-indexing in <5 minutes.
- Support custom mappings via configuration.
- Identify join paths with 95% accuracy using foreign key metadata and LLM reasoning.
- Track schema versions and changes.

### 5.3 Query Construction Agent (LLM-Based with PydanticAI)

**Features:**
- SQL query generation using LLM to select and fill parameterized templates.
- Join path optimization via SQLAlchemy Core metadata and LLM suggestions.
- Subquery/CTE generation for complex queries.
- Multi-dialect support.

**Tech Stack:**
- **PydanticAI**: Defines the agent as a Pydantic model with LLM-powered methods for SQL template selection and filling based on intent and mappings.
- **SQLAlchemy Core**: For query parameterization, dialect support, and execution.
- **DSPy**: Optimizes template selection and query generation prompts.
- **Pydantic**: Core structure for inputs (e.g., `QueryConstructionInput`) and outputs (e.g., `QueryConstructionOutput`).
- **FastAPI**: API serving.

**Requirements:**
- Generate syntactically correct, optimized queries for PostgreSQL, MySQL, SQL Server, Oracle, and SQLite.
- Support all CRUD operations and complex patterns (aggregations, joins, subqueries, CTEs, window functions).
- Use join conditions based on foreign keys or LLM-inferred relationships.
- Handle edge cases (NULLs, large datasets, time-series).

### 5.4 Validation & Safety Agent (LLM-Based with PydanticAI)

**Features:**
- SQL injection prevention via parameterized queries.
- Query complexity analysis using LLM.
- Permission enforcement using database roles.
- Performance estimation with LLM assistance.
- Business rule validation.

**Tech Stack:**
- **PydanticAI**: Defines the agent as a Pydantic model with LLM-powered methods to analyze query safety, complexity, and suggest optimizations.
- **SQLAlchemy Core**: Parameterized queries and connection management.
- **Database Roles**: For access control.
- **DSPy**: Optimizes validation prompts.
- **Pydantic**: Core structure for inputs (e.g., `ValidationInput`) and outputs (e.g., `ValidationOutput`).
- **FastAPI**: API serving.

**Requirements:**
- Prevent 100% of SQL injection attempts via parameterization.
- Enforce database-native permissions.
- Reject queries exceeding resource limits (e.g., >10s execution) with LLM-assisted estimation.
- Require confirmation for destructive operations (e.g., DELETE).

### 5.5 Explanation Agent (LLM-Based with PydanticAI)

**Features:**
- SQL-to-natural-language translation.
- Visualization configuration generation.
- Result format preview.
- Educational content.

**Tech Stack:**
- **PydanticAI**: Defines the agent as a Pydantic model with LLM-powered methods to generate explanations and visualization configs.
- **DSPy**: Optimizes prompts for clarity and relevance.
- **Pydantic**: Core structure for inputs (e.g., `ExplanationInput`) and outputs (e.g., `ExplanationOutput`).
- **FastAPI**: API serving.
- **React.js + Chart.js**: Renders visualizations.

**Requirements:**
- Provide clear explanations in non-technical terms within 2s.
- Suggest visualization types (e.g., bar, line) based on data.
- Preview result structure pre-execution.
- Offer SQL learning tips.

### 5.6 Prompt Optimization (via DSPy)

**Features:**
- Automatic prompt tuning for all LLM-based agents.
- Feedback collection for continuous improvement.

**Tech Stack:**
- **DSPy**: Built-in optimizers (e.g., BootstrapFewShot) for prompt refinement.
- **PostgreSQL**: Stores feedback and performance metrics.

**Requirements:**
- Collect feedback on query accuracy and usefulness.
- Retrain prompts monthly using feedback.
- Prioritize high-impact queries for optimization.

## 6. System Integration Requirements

### 6.1 Database Connectivity

**Tech Stack:** SQLAlchemy Core for multi-database support (PostgreSQL, MySQL, SQL Server, Oracle, SQLite).

**Features:**
- Connection pooling with configurable limits.
- Read-only mode toggle.
- Credential management via environment variables.
- SSL and SSH tunneling support.

**Optimization:**
- Use pool_size=20, max_overflow=10 for connection pooling.
- Implement caching for query plans and results to improve performance.

### 6.2 API & Access

**Tech Stack:** FastAPI with OpenAPI specification.

**Features:**
- RESTful APIs for all agents.
- API key authentication.
- SDKs in Python and JavaScript.

### 6.3 User Interfaces

**Web UI:**
- **Tech Stack:** React.js (desktop-only, no mobile responsiveness).
- **Features:** Query input, SQL output, history, visualizations via Chart.js.

**CLI:**
- **Tech Stack:** Click (Python).
- **Features:** Command-line query submission and result display.

**BI Tool Integration:** Deferred to Phase 4 (Months 10-12).

## 7. Non-Functional Requirements

### 7.1 Performance

- Query translation <1s for standard queries.
- Support 100+ concurrent users with caching.
- 99.9% uptime.
- Graceful degradation under load.

### 7.2 Security

- Encrypt data in transit (TLS) and at rest (AES-256).
- Audit logging for all queries/actions.
- Comply with GDPR, CCPA, SOC 2.
- Regular security scans.

### 7.3 Scalability

- Support horizontal scaling to handle increased load.
- Enable multi-region deployment for global access.
- Implement batch processing for large analytics queries.

## 8. Implementation Phases

### Phase 1: Core Functionality (Months 1-3)

- User Intent Agent (PydanticAI).
- Schema Mapping Agent (PydanticAI).
- Basic Query Construction (SELECT queries, PydanticAI-based template selection).
- Validation & Safety Agent (PydanticAI).
- Web UI (React.js) and CLI (Click).
- PostgreSQL support.

### Phase 2: Enhanced Capabilities (Months 4-6)

- Full Query Construction (CRUD, joins, aggregations).
- Explanation Agent (PydanticAI).
- Multi-turn conversation support.
- MySQL and SQL Server support.

### Phase 3: Production Readiness (Months 7-9)

- Complex queries (subqueries, CTEs, window functions).
- Prompt optimization via DSPy for all agents.
- Oracle and SQLite support.
- Enterprise integrations (e.g., SSO).

### Phase 4: Advanced Features (Months 10-12)

- Recursive queries and cross-database queries.
- BI tool integration (REST API).
- Visualization enhancements.
- NoSQL support (e.g., MongoDB).

## 9. Dependencies

- **Libraries:** PydanticAI, Hugging Face Transformers, SQLAlchemy Core, FastAPI, DSPy, Pydantic.
- **Expertise:** Database optimization, security compliance, NLP/LLM fine-tuning, prompt engineering, PydanticAI development.

## 10. Success Criteria

- 85% query accuracy across supported databases.
- Performance meets all requirements in production.
- 95% user satisfaction.
- Zero critical security vulnerabilities.
- 40% adoption among non-technical users.
- Handles 1000+ queries/day with <1% error rate.

## 11. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Inaccurate query generation | High | Medium | Robust testing, human-in-the-loop, hybrid approaches |
| Performance bottlenecks | Medium | Medium | Load testing, caching, optimization |
| Security vulnerabilities | High | Low | Audits, encryption, least privilege, parameterized queries |
| User adoption challenges | Medium | Medium | Training, intuitive UI, phased rollout |
| NLP complexity | High | Medium | Pre-trained models, DSPy retraining, prompt engineering |
| PydanticAI learning curve | Medium | Medium | Training, documentation, community support |

## 12. Decision Log

| Date | Decision | Rationale | Alternatives |
|------|----------|-----------|--------------|
| TBD | Use PydanticAI for agent development | Structured agent definitions, type safety, native Pydantic integration | LangChain, Llama Index, AutoGen, smolagents |
| TBD | Hybrid approach for Query Construction | Balance between LLM flexibility and template security | Pure LLM, rule-based |

## 13. Glossary

- **Multi-turn Conversation:** Context retention across multiple inputs.
- **Schema Evolution:** Adapting to database structure changes.
- **LLM-Based Agent:** An agent that uses a Large Language Model for its core functionality.
- **PydanticAI:** A framework for building LLM-powered Pydantic model-based agents with type safety and structured interactions.

## 14. Appendix

### A. User Journey Example

User: "Find average order value by customer."
System: Intent → Schema Mapping → Query Construction → Validation → Execution → Explanation.
Output: SQL query, results, explanation, and visualization.

### B. Database Support Roadmap

| Database | Phase | Completion |
|----------|-------|------------|
| PostgreSQL | 1 | Month 3 |
| MySQL, SQL Server | 2 | Month 6 |
| Oracle, SQLite | 3 | Month 9 |
| NoSQL (MongoDB) | 4 | Month 12 |
