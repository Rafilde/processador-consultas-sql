window.addEventListener('DOMContentLoaded', () => {
    loadMetadata();
});

async function loadMetadata() {
    try {
        const response = await fetch('/metadata');
        const metadata = await response.json();
        
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
                <pre>${result.query}</pre>
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
                <pre>${result.query}</pre>
            `;
            resultContent.appendChild(detailsDiv);
        }
    }

    resultPanel.classList.add('show');
    resultPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

document.getElementById('sqlQuery').addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        validateQuery();
    }
});