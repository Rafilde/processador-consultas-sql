window.loadMetadata = async function() {
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
};

// ==================== LÓGICA DO MENU ====================
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
        // Colapsar
        header.classList.remove('expanded');
        header.setAttribute('aria-expanded', 'false');
        content.style.maxHeight = '0';
    } else {
        // Expandir
        header.classList.add('expanded');
        header.setAttribute('aria-expanded', 'true');
        content.style.maxHeight = content.scrollHeight + 'px';
    }
}