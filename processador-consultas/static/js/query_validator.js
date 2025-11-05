window.initializeResultOutput = function() {
    const mainPanel = document.querySelector('.main-panel');
    const buttonContainer = mainPanel.querySelector('.btn-container');
    const resultOutput = document.createElement('div');
    resultOutput.id = 'resultOutput';
    resultOutput.className = 'result-output';
    mainPanel.insertBefore(resultOutput, buttonContainer);
};

window.validateQuery = async function() {
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
        const escapedError = typeof escapeHtml === 'function' ? escapeHtml(error.message) : error.message;
        resultOutput.innerHTML = '<div class="result-error"><p>Erro ao validar consulta</p><p>' + escapedError + '</p></div>';
    }
};

function displayResult(result) {
    const resultOutput = document.getElementById('resultOutput');

    resultOutput.innerHTML = '';
    
    const escape = typeof escapeHtml === 'function' ? escapeHtml : (text) => text;

    if (result.valid) {
        const detailsDiv = document.createElement('div');
        detailsDiv.className = 'result-details';
        
        let detailsHTML = '<p><strong>Query normalizada:</strong></p>';
        detailsHTML += `<pre>${escape(result.query)}</pre>`;
        
        if (result.tables_found && result.tables_found.length > 0) {
            detailsHTML += `<p><strong>Tabelas detectadas:</strong> ${result.tables_found.join(', ')}</p>`;
        }
        
        if (result.attributes_found && result.attributes_found.length > 0) {
            detailsHTML += `<p><strong>Atributos detectados:</strong> ${result.attributes_found.join(', ')}</p>`;
        }

        if (result.relational_algebra) {
            detailsHTML += '<p><strong>Conversão para Álgebra Relacional:</strong></p>';
            detailsHTML += `<pre>${escape(result.relational_algebra)}</pre>`;
        }
        
        detailsDiv.innerHTML = detailsHTML;
        resultOutput.appendChild(detailsDiv);
        
        // HU3: Renderizar Grafo de Operadores
        if (result.operator_graph) {
            const graphSection = document.createElement('div');
            graphSection.className = 'graph-section';
            graphSection.innerHTML = '<h3>📊 Grafo de Operadores (HU3)</h3>';
            resultOutput.appendChild(graphSection);
            
            // Renderizar o grafo usando Vis.js
            if (typeof window.renderOperatorGraph === 'function') {
                window.renderOperatorGraph(result.operator_graph);
            } else {
                graphSection.innerHTML += '<p class="error">Erro: Visualizador de grafo não carregado</p>';
            }
        }
        
    } else {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'result-error';
        
        let errorHTML = '<p>Erros encontrados:</p>';
        
        if (result.errors && result.errors.length > 0) {
            result.errors.forEach(error => {
                errorHTML += `<p>${escape(error)}</p>`;
            });
        }
        
        errorDiv.innerHTML = errorHTML;
        resultOutput.appendChild(errorDiv);
    }

    resultOutput.classList.add('show');
}