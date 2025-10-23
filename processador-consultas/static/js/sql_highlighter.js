window.initializeSQLHighlighter = function() {
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
};

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
    
    const tables = new Set(Object.keys(window.metadata || {})); 
    
    const keywords = new Set([
        'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 
        'OUTER', 'ON', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
        'ORDER', 'BY', 'GROUP', 'HAVING', 'DISTINCT', 'AS', 'NULL',
        'IS', 'EXISTS', 'UNION', 'ALL', 'LIMIT', 'OFFSET', 'ASC', 'DESC'
    ]);
    
    const operators = ['<=', '>=', '<>', '!=', '=', '>', '<', '+', '-', '*', '/', '%'];
    
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