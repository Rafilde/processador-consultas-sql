window.addEventListener('DOMContentLoaded', () => {
    loadMetadata();
    initializeSQLHighlighter();
    initializeResultOutput();
});

// ==================== INITIALIZE RESULT OUTPUT ====================
function initializeResultOutput() {
    const mainPanel = document.querySelector('.main-panel');
    const buttonContainer = mainPanel.querySelector('.btn-container');
    const resultOutput = document.createElement('div');
    resultOutput.id = 'resultOutput';
    resultOutput.className = 'result-output';
    mainPanel.insertBefore(resultOutput, buttonContainer);
}

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
            
            const header = document.createElement('button');
            header.className = 'table-card-header';
            header.innerHTML = `<span>${tableName.toUpperCase()}</span><span class="expander">▶</span>`;
            header.setAttribute('aria-expanded', 'false');
            header.setAttribute('aria-controls', `content-${tableName}`);
            
            const content = document.createElement('div');
            content.className = 'table-card-content';
            content.id = `content-${tableName}`;
            
            const fieldList = document.createElement('ul');
            fields.forEach(field => {
                const li = document.createElement('li');
                li.textContent = field;
                fieldList.appendChild(li);
            });
            
            content.appendChild(fieldList);
            
            header.addEventListener('click', () => toggleAccordion(header, content));
            
            tablesGrid.appendChild(header);
            tablesGrid.appendChild(content);
        }
        
    } catch (error) {
        console.error('Erro ao carregar metadados:', error);
        const metadataPanel = document.getElementById('metadataPanel');
        metadataPanel.innerHTML = '<p style="color: #ef4444; padding: 1rem;">Erro ao carregar o esquema do banco de dados. Tente recarregar a página.</p>';
        metadataPanel.style.display = 'block';
    }
}

// ==================== LÓGICA DO ViSUALIZADOR DA TABELA  ====================
function toggleAccordion(header, content) {
    document.querySelectorAll('.table-card-header.expanded').forEach(h => {
        if (h !== header) {
            h.classList.remove('expanded');
            h.setAttribute('aria-expanded', 'false');
            document.getElementById(h.getAttribute('aria-controls')).style.maxHeight = '0';
        }
    });

    const isExpanded = header.classList.contains('expanded');
    
    if (isExpanded) {
        header.classList.remove('expanded');
        header.setAttribute('aria-expanded', 'false');
        content.style.maxHeight = '0';
    } else {
        header.classList.add('expanded');
        header.setAttribute('aria-expanded', 'true');
        content.style.maxHeight = content.scrollHeight + 'px';
    }
}

// ==================== QUERY VALIDATOR ====================
async function validateQuery() {
    const query = document.getElementById('sqlQuery').value;
    const resultOutput = document.getElementById('resultOutput');
    
    if (!query.trim()) {
        alert('Por favor, digite uma consulta SQL');
        return;
    }
    
    resultOutput.classList.remove('show');
    resultOutput.innerHTML = '<p class="loading-inline"><span class="spinner-inline"></span>Processando validação...</p>';
    resultOutput.classList.add('show');
    
    try {
        const response = await fetch('/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });
        
        const result = await response.json();
        displayResult(result);
        
    } catch (error) {
        resultOutput.innerHTML = '<div class="result-error"><p>Erro ao validar consulta</p><p>' + escapeHtml(error.message) + '</p></div>';
    }
}

function displayResult(result) {
    const resultOutput = document.getElementById('resultOutput');

    resultOutput.innerHTML = '';
    
    if (result.valid) {
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'result-details';
        
        let detailsHTML = '<p><strong>Query normalizada:</strong></p>';
        detailsHTML += `<pre>${escapeHtml(result.query)}</pre>`;
        
        if (result.tables_found && result.tables_found.length > 0) {
            detailsHTML += `<p><strong>Tabelas detectadas:</strong> ${result.tables_found.join(', ')}</p>`;
        }
        
        if (result.attributes_found && result.attributes_found.length > 0) {
            detailsHTML += `<p><strong>Atributos detectados:</strong> ${result.attributes_found.join(', ')}</p>`;
        }
        
        detailsDiv.innerHTML = detailsHTML;
        resultOutput.appendChild(detailsDiv);
        
    } else {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'result-error';
        
        let errorHTML = '<p>Erros encontrados:</p>';
        
        if (result.errors && result.errors.length > 0) {
            result.errors.forEach(error => {
                errorHTML += `<p>${escapeHtml(error)}</p>`;
            });
        }
        
        errorDiv.innerHTML = errorHTML;
        resultOutput.appendChild(errorDiv);
    }

    resultOutput.classList.add('show');
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

// ==================== TOGGLE METADATA ====================
function toggleMetadata() {
    const metadataPanel = document.getElementById('metadataPanel');
    const button = document.querySelector('.btn-secondary');
    const isVisible = metadataPanel.style.display !== 'none';
    
    if (isVisible) {
        metadataPanel.classList.remove('show');
        setTimeout(() => {
            metadataPanel.style.display = 'none';
        }, 300); 
        button.textContent = 'Ver Tabelas';
    } else {
        metadataPanel.style.display = 'block';
        setTimeout(() => {
            metadataPanel.classList.add('show');
        }, 10); 
        button.textContent = 'Ocultar Tabelas';
        
        setTimeout(() => {
            metadataPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 310);
    }
}