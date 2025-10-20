window.addEventListener('DOMContentLoaded', () => {
    loadMetadata();
    initializeSQLHighlighter();
});

// ==================== SQL SYNTAX HIGHLIGHTER ====================
function initializeSQLHighlighter() {
    const sqlInput = document.getElementById('sqlQuery');

    const wrapper = document.createElement('div');
    wrapper.className = 'sql-input-wrapper';
    
    const highlight = document.createElement('div');
    highlight.className = 'sql-highlight';
    highlight.setAttribute('aria-hidden', 'true');
    
    sqlInput.parentNode.insertBefore(wrapper, sqlInput);
    wrapper.appendChild(highlight);
    wrapper.appendChild(sqlInput);
    
    sqlInput.addEventListener('scroll', () => {
        highlight.scrollTop = sqlInput.scrollTop;
        highlight.scrollLeft = sqlInput.scrollLeft;
    });
    
    sqlInput.addEventListener('input', () => updateHighlight(sqlInput, highlight));
    
    updateHighlight(sqlInput, highlight);
}

function updateHighlight(textarea, highlight) {
    const text = textarea.value;
    
    if (!text) {
        highlight.innerHTML = '&nbsp;';
        return;
    }
    
    const highlighted = highlightSQL(text);
    highlight.innerHTML = highlighted + '&nbsp;';
}

function highlightSQL(text) {
    const tokens = tokenizeSQL(text);
    
    return tokens.map(token => {
        const escaped = escapeHtml(token.value);
        
        switch (token.type) {
            case 'keyword':
                return `<span class="sql-keyword">${escaped}</span>`;
            case 'table':
                return `<span class="sql-table">${escaped}</span>`;
            case 'column':
                return `<span class="sql-column">${escaped}</span>`;
            case 'string':
                return `<span class="sql-string">${escaped}</span>`;
            case 'number':
                return `<span class="sql-number">${escaped}</span>`;
            case 'operator':
                return `<span class="sql-operator">${escaped}</span>`;
            case 'comment':
                return `<span class="sql-comment">${escaped}</span>`;
            default:
                return escaped;
        }
    }).join('');
}

function tokenizeSQL(text) {
    const tokens = [];
    let i = 0;
    
    const keywords = new Set([
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 
        'OUTER', 'ON', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
        'ORDER', 'BY', 'GROUP', 'HAVING', 'DISTINCT', 'AS', 'NULL',
        'IS', 'EXISTS', 'UNION', 'ALL', 'LIMIT', 'OFFSET', 'ASC', 'DESC'
    ]);
    
    const operators = ['<=', '>=', '<>', '!=', '=', '>', '<', '+', '-', '*', '/', '%'];
    
    const tables = new Set(Object.keys(window.metadata || {}));
    
    while (i < text.length) {
        const char = text[i];

        if (char === '-' && text[i + 1] === '-') {
            let comment = '';
            while (i < text.length && text[i] !== '\n') {
                comment += text[i];
                i++;
            }
            tokens.push({ type: 'comment', value: comment });
            continue;
        }
        
        if (char === "'" || char === '"') {
            const quote = char;
            let string = quote;
            i++;
            
            while (i < text.length) {
                if (text[i] === quote) {
                    string += text[i];
                    i++;
                    break;
                }
                if (text[i] === '\\' && i + 1 < text.length) {
                    string += text[i] + text[i + 1];
                    i += 2;
                } else {
                    string += text[i];
                    i++;
                }
            }
            
            tokens.push({ type: 'string', value: string });
            continue;
        }
        
        if (/\d/.test(char)) {
            let number = '';
            while (i < text.length && /[\d.]/.test(text[i])) {
                number += text[i];
                i++;
            }
            tokens.push({ type: 'number', value: number });
            continue;
        }
        
        let operatorFound = false;
        for (const op of operators) {
            if (text.substr(i, op.length) === op) {
                tokens.push({ type: 'operator', value: op });
                i += op.length;
                operatorFound = true;
                break;
            }
        }
        if (operatorFound) continue;

        if (/[a-zA-Z_]/.test(char)) {
            let word = '';
            let startPos = i;
            
            while (i < text.length && /[a-zA-Z0-9_]/.test(text[i])) {
                word += text[i];
                i++;
            }
            
            const upperWord = word.toUpperCase();

            if (i < text.length && text[i] === '.') {
                if (tables.has(word)) {
                    tokens.push({ type: 'table', value: word });
                } else {
                    tokens.push({ type: 'table', value: word });
                }
                tokens.push({ type: 'text', value: '.' });
                i++;

                if (i < text.length && /[a-zA-Z_]/.test(text[i])) {
                    let column = '';
                    while (i < text.length && /[a-zA-Z0-9_]/.test(text[i])) {
                        column += text[i];
                        i++;
                    }
                    tokens.push({ type: 'column', value: column });
                }
            } else if (keywords.has(upperWord)) {
                tokens.push({ type: 'keyword', value: word.toUpperCase() });
            } else if (tables.has(word)) {
                tokens.push({ type: 'table', value: word });
            } else {
                tokens.push({ type: 'text', value: word });
            }
            
            continue;
        }
        
        tokens.push({ type: 'text', value: char });
        i++;
    }
    
    return tokens;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ==================== METADATA LOADER ====================
async function loadMetadata() {
    try {
        const response = await fetch('/metadata');
        const metadata = await response.json();
        window.metadata = metadata;
        
        const tablesGrid = document.getElementById('tablesGrid');
        tablesGrid.innerHTML = '';
        
        for (const [tableName, fields] of Object.entries(metadata)) {
            const tableCard = document.createElement('div');
            tableCard.className = 'table-card';
            
            const title = document.createElement('h3');
            title.textContent = tableName;
            tableCard.appendChild(title);
            
            const fieldList = document.createElement('ul');
            fields.forEach(field => {
                const li = document.createElement('li');
                li.textContent = field;
                fieldList.appendChild(li);
            });
            
            tableCard.appendChild(fieldList);
            tablesGrid.appendChild(tableCard);
        }
    } catch (error) {
        console.error('Erro ao carregar metadados:', error);
    }
}

// ==================== QUERY VALIDATOR ====================
async function validateQuery() {
    const query = document.getElementById('sqlQuery').value;
    const loading = document.getElementById('loading');
    const resultPanel = document.getElementById('resultPanel');
    
    if (!query.trim()) {
        alert('Por favor, digite uma consulta SQL');
        return;
    }
    
    loading.classList.add('show');
    resultPanel.classList.remove('show');
    
    try {
        const response = await fetch('/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        const result = await response.json();
        
        loading.classList.remove('show');
        displayResult(result);
        
    } catch (error) {
        loading.classList.remove('show');
        alert('Erro ao validar consulta: ' + error.message);
    }
}

function displayResult(result) {
    const resultPanel = document.getElementById('resultPanel');
    const resultHeader = document.getElementById('resultHeader');
    const resultIcon = document.getElementById('resultIcon');
    const resultTitle = document.getElementById('resultTitle');
    const resultContent = document.getElementById('resultContent');

    resultContent.innerHTML = '';
    
    if (result.valid) {
        resultHeader.className = 'result-header valid';
        resultIcon.textContent = '✓';
        resultIcon.style.color = '#10b981';
        resultTitle.textContent = 'Consulta Válida!';
        resultTitle.style.color = '#047857';
        
        const successBox = document.createElement('div');
        successBox.className = 'success-box';
        successBox.innerHTML = `
            <h3>✓ A consulta passou em todas as validações</h3>
            <ul>
                <li>Sintaxe SQL válida</li>
                <li>Comandos permitidos (SELECT, FROM, WHERE, JOIN, ON)</li>
                <li>Tabelas existem no modelo</li>
                <li>Atributos são válidos</li>
                <li>Operadores permitidos (=, >, <, <=, >=, <>, AND)</li>
                <li>Parênteses balanceados</li>
            </ul>
        `;
        resultContent.appendChild(successBox);
        
        if (result.tables_found && result.tables_found.length > 0) {
            const detailsDiv = document.createElement('div');
            detailsDiv.className = 'details-box';
            detailsDiv.innerHTML = `
                <h3>Detalhes da Análise:</h3>
                <p><strong>Consulta normalizada:</strong></p>
                <pre>${escapeHtml(result.query)}</pre>
                <p style="margin-top: 1rem;"><strong>Tabelas encontradas:</strong> ${result.tables_found.join(', ')}</p>
            `;
            resultContent.appendChild(detailsDiv);
        }
        
    } else {
        resultHeader.className = 'result-header invalid';
        resultIcon.textContent = '✗';
        resultIcon.style.color = '#ef4444';
        resultTitle.textContent = 'Consulta Inválida';
        resultTitle.style.color = '#dc2626';
        
        if (result.errors && result.errors.length > 0) {
            const errorBox = document.createElement('div');
            errorBox.className = 'error-box';
            
            const errorTitle = document.createElement('h3');
            errorTitle.textContent = '✗ Erros encontrados:';
            errorBox.appendChild(errorTitle);
            
            const errorList = document.createElement('ul');
            errorList.className = 'error-list';
            
            result.errors.forEach(error => {
                const li = document.createElement('li');
                li.textContent = error;
                errorList.appendChild(li);
            });
            
            errorBox.appendChild(errorList);
            resultContent.appendChild(errorBox);
        }
        
        if (result.query) {
            const detailsDiv = document.createElement('div');
            detailsDiv.className = 'details-box';
            detailsDiv.innerHTML = `
                <h3>Consulta Analisada:</h3>
                <pre>${escapeHtml(result.query)}</pre>
            `;
            resultContent.appendChild(detailsDiv);
        }
    }

    resultPanel.classList.add('show');
    resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ==================== KEYBOARD SHORTCUTS ====================
document.addEventListener('DOMContentLoaded', () => {
    const sqlInput = document.getElementById('sqlQuery');
    if (sqlInput) {
        sqlInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                validateQuery();
            }
        });
    }
});