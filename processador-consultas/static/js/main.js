
window.addEventListener('DOMContentLoaded', () => {
    loadMetadata(); 
    initializeSQLHighlighter(); 
    initializeResultOutput();
    initializeKeyboardShortcuts();
});

// ==================== KEYBOARD SHORTCUTS ====================
function initializeKeyboardShortcuts() {
    const sqlInput = document.getElementById('sqlQuery');
    if (sqlInput) {
        sqlInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                validateQuery(); 
            }
        });
    }
}

// ==================== VISUALIZAÇÃO DA TABELA ====================
function toggleMetadata() {
    const metadataPanel = document.getElementById('metadataPanel');
    const button = document.querySelector('.btn-secondary');
    
    const isVisible = metadataPanel.style.display !== 'none';
    
    if (isVisible) {
        // Ocultar
        metadataPanel.classList.remove('show');
        setTimeout(() => {
            metadataPanel.style.display = 'none';
        }, 300); 
        button.textContent = 'Ver Tabelas';
    } else {
        // Exibir
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