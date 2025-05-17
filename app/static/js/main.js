// Global Variables
let sqlEditor;
let currentResults = null;
let currentPage = 0;
let resultsPerPage = 10;
let conversationId = null;

// API Base URL
const API_BASE_URL = '/api/v1';

// DOM Elements
const queryForm = document.getElementById('queryForm');
const queryInput = document.getElementById('queryInput');
const executeQueryCheckbox = document.getElementById('executeQuery');
const explanationTypeSelect = document.getElementById('explanationType');
const agentTypeSelect = document.getElementById('agentType');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultArea = document.getElementById('resultArea');
const sqlWarnings = document.getElementById('sqlWarnings');
const explanation = document.getElementById('explanation');
const queryResultCard = document.getElementById('queryResultCard');
const resultsTableHead = document.getElementById('resultsTableHead');
const resultsTableBody = document.getElementById('resultsTableBody');
const resultsCount = document.getElementById('resultsCount');
const prevPageBtn = document.getElementById('prevPageBtn');
const nextPageBtn = document.getElementById('nextPageBtn');
const copySqlBtn = document.getElementById('copySqlBtn');
const showSchemaBtn = document.getElementById('showSchemaBtn');
const schemaModal = new bootstrap.Modal(document.getElementById('schemaModal'));
const schemaBody = document.getElementById('schemaBody');

// Initialize CodeMirror for SQL display
document.addEventListener('DOMContentLoaded', () => {
    sqlEditor = CodeMirror(document.getElementById('sqlEditor'), {
        mode: 'text/x-sql',
        theme: 'default',
        lineNumbers: true,
        readOnly: true,
        lineWrapping: true
    });

    // Set up event listeners
    queryForm.addEventListener('submit', handleQuerySubmit);
    copySqlBtn.addEventListener('click', copyGeneratedSQL);
    showSchemaBtn.addEventListener('click', showDatabaseSchema);
    prevPageBtn.addEventListener('click', () => navigateResults(-1));
    nextPageBtn.addEventListener('click', () => navigateResults(1));
});

// Handle query form submission
async function handleQuerySubmit(event) {
    event.preventDefault();
    
    const query = queryInput.value.trim();
    if (!query) {
        alert('Please enter a query.');
        return;
    }
    
    // Show loading indicator
    loadingIndicator.classList.remove('d-none');
    resultArea.classList.add('d-none');
    
    try {
        // Prepare the request
        const requestData = {
            query: query,
            conversation_id: conversationId,
            explanation_type: explanationTypeSelect.value,
            execute_query: executeQueryCheckbox.checked,
            agent_type: agentTypeSelect.value
        };
        
        // Send request to API
        const response = await fetch(`${API_BASE_URL}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Store conversation ID for follow-up queries
        conversationId = data.conversation_id;
        
        // Display the results
        displayResults(data.user_response);
        
        // Show agent type info
        let agentTypeInfo = '';
        if (data.optimized_agent_used) {
            agentTypeInfo = 'Used optimized (DSPy) agents';
        } else if (data.enhanced_agent_used) {
            agentTypeInfo = 'Used enhanced (PydanticAI) agents';
        } else {
            agentTypeInfo = 'Used base agents';
        }
        
        // Add agent info to explanation section
        const agentInfoElement = document.createElement('div');
        agentInfoElement.className = 'mt-3 text-muted small';
        agentInfoElement.innerHTML = `<i class="fas fa-info-circle me-1"></i>${agentTypeInfo}`;
        explanation.appendChild(agentInfoElement);
        
    } catch (error) {
        console.error('Error processing query:', error);
        alert(`Error: ${error.message}`);
    } finally {
        // Hide loading indicator
        loadingIndicator.classList.add('d-none');
    }
}

// Display query results
function displayResults(response) {
    // Show the result area
    resultArea.classList.remove('d-none');
    
    // Display SQL
    sqlEditor.setValue(response.sql_generation.sql);
    sqlEditor.refresh();
    
    // Display warnings if any
    sqlWarnings.innerHTML = '';
    if (response.sql_generation.warnings && response.sql_generation.warnings.length > 0) {
        const warningsList = document.createElement('ul');
        warningsList.className = 'list-unstyled mb-0';
        
        response.sql_generation.warnings.forEach(warning => {
            const warningItem = document.createElement('li');
            warningItem.className = 'sql-warning';
            warningItem.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>${warning}`;
            warningsList.appendChild(warningItem);
        });
        
        sqlWarnings.appendChild(warningsList);
    }
    
    // Display explanation
    explanation.textContent = response.explanation.text;
    
    // Display query results if available
    if (response.query_result && response.query_result.status === 'SUCCESS') {
        currentResults = response.query_result;
        currentPage = 0;
        displayQueryResults();
        queryResultCard.classList.remove('d-none');
    } else {
        queryResultCard.classList.add('d-none');
        currentResults = null;
    }
}

// Display query results with pagination
function displayQueryResults() {
    if (!currentResults || !currentResults.rows || currentResults.rows.length === 0) {
        queryResultCard.classList.add('d-none');
        return;
    }
    
    // Calculate pagination
    const totalPages = Math.ceil(currentResults.rows.length / resultsPerPage);
    const startIndex = currentPage * resultsPerPage;
    const endIndex = Math.min(startIndex + resultsPerPage, currentResults.rows.length);
    const currentRows = currentResults.rows.slice(startIndex, endIndex);
    
    // Update pagination controls
    prevPageBtn.disabled = currentPage === 0;
    nextPageBtn.disabled = currentPage >= totalPages - 1;
    resultsCount.textContent = `Showing ${startIndex + 1} to ${endIndex} of ${currentResults.rows.length} results`;
    
    // Create table headers
    resultsTableHead.innerHTML = '';
    const headerRow = document.createElement('tr');
    
    currentResults.column_names.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column;
        headerRow.appendChild(th);
    });
    
    resultsTableHead.appendChild(headerRow);
    
    // Create table rows
    resultsTableBody.innerHTML = '';
    
    currentRows.forEach(row => {
        const tr = document.createElement('tr');
        
        currentResults.column_names.forEach(column => {
            const td = document.createElement('td');
            td.textContent = row[column] !== null ? row[column] : '';
            tr.appendChild(td);
        });
        
        resultsTableBody.appendChild(tr);
    });
}

// Navigate between result pages
function navigateResults(direction) {
    const newPage = currentPage + direction;
    if (newPage >= 0 && newPage < Math.ceil(currentResults.rows.length / resultsPerPage)) {
        currentPage = newPage;
        displayQueryResults();
    }
}

// Copy generated SQL to clipboard
function copyGeneratedSQL() {
    const sql = sqlEditor.getValue();
    navigator.clipboard.writeText(sql)
        .then(() => {
            const originalText = copySqlBtn.innerHTML;
            copySqlBtn.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
            setTimeout(() => {
                copySqlBtn.innerHTML = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy SQL: ', err);
            alert('Failed to copy SQL to clipboard');
        });
}

// Show database schema
async function showDatabaseSchema() {
    try {
        schemaBody.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading database schema...</p>
            </div>
        `;
        
        schemaModal.show();
        
        const response = await fetch(`${API_BASE_URL}/schema`);
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const schema = await response.json();
        displaySchema(schema);
        
    } catch (error) {
        console.error('Error fetching schema:', error);
        schemaBody.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle me-2"></i>
                Error loading schema: ${error.message}
            </div>
        `;
    }
}

// Display database schema
function displaySchema(schema) {
    let html = `<h4 class="mb-3">Database: ${schema.name}</h4>`;
    
    if (schema.tables.length === 0) {
        html += `<div class="alert alert-info">No tables found in the database.</div>`;
    } else {
        schema.tables.forEach(table => {
            html += `
                <div class="schema-table">
                    <div class="schema-table-name">
                        <i class="fas fa-table me-2"></i>${table.name}
                    </div>
            `;
            
            if (table.description) {
                html += `<div class="schema-table-description">${table.description}</div>`;
            }
            
            html += `
                <div class="table-responsive">
                    <table class="table table-sm table-bordered">
                        <thead class="table-light">
                            <tr>
                                <th>Column</th>
                                <th>Type</th>
                                <th>Nullable</th>
                                <th>Key</th>
                                <th>Foreign Key</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            table.columns.forEach(column => {
                html += `
                    <tr>
                        <td class="${column.primary_key ? 'schema-column-pk' : column.foreign_key ? 'schema-column-fk' : ''}">
                            ${column.name}
                        </td>
                        <td>${column.data_type}</td>
                        <td>${column.nullable ? 'Yes' : 'No'}</td>
                        <td>${column.primary_key ? 'Primary' : ''}</td>
                        <td>${column.foreign_key || ''}</td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            </div>
            `;
        });
    }
    
    schemaBody.innerHTML = html;
} 