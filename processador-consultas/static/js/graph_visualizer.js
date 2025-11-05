/**
 * graph_visualizer.js
 * Visualizador de Grafo de Operadores para HU3
 * Usa Vis.js para renderizar o grafo
 */

window.renderOperatorGraph = function(graphData) {
    if (!graphData || !graphData.nodes || !graphData.edges) {
        console.error('Dados do grafo inválidos');
        return;
    }

    // Criar container para o grafo se não existir
    let graphContainer = document.getElementById('graphContainer');
    if (!graphContainer) {
        graphContainer = document.createElement('div');
        graphContainer.id = 'graphContainer';
        graphContainer.className = 'graph-container';
        
        const resultOutput = document.getElementById('resultOutput');
        if (resultOutput) {
            // Adicionar legenda antes do grafo
            const legend = createLegend();
            resultOutput.appendChild(legend);
            resultOutput.appendChild(graphContainer);
        }
    }

    // Preparar nós para Vis.js
    const visNodes = graphData.nodes.map(node => {
        const colors = getNodeColor(node.type);
        const shape = getNodeShape(node.type);
        
        let label = formatNodeLabel(node);
        
        return {
            id: node.id,
            label: label,
            shape: shape,
            color: colors,
            font: {
                size: 16,
                color: '#ffffff',
                face: 'monospace',
                bold: true
            },
            margin: 10,
            title: getNodeTooltip(node) // Tooltip ao passar o mouse
        };
    });

    // Preparar arestas para Vis.js
    const visEdges = graphData.edges.map(edge => {
        return {
            from: edge.from,
            to: edge.to,
            arrows: {
                to: {
                    enabled: true,
                    scaleFactor: 0.8
                }
            },
            color: {
                color: '#848484',
                highlight: '#2b7ce9'
            },
            width: 2,
            smooth: {
                type: 'cubicBezier',
                forceDirection: 'vertical'
            }
        };
    });

    // Configuração do grafo
    const data = {
        nodes: new vis.DataSet(visNodes),
        edges: new vis.DataSet(visEdges)
    };

    const options = {
        layout: {
            hierarchical: {
                enabled: true,
                direction: 'UD', // Up-Down (de baixo para cima)
                sortMethod: 'directed',
                nodeSpacing: 150,
                levelSeparation: 120,
                treeSpacing: 200
            }
        },
        physics: {
            enabled: false
        },
        interaction: {
            dragNodes: true,
            dragView: true,
            zoomView: true,
            hover: true,
            tooltipDelay: 100
        },
        nodes: {
            borderWidth: 2,
            borderWidthSelected: 3,
            shadow: {
                enabled: true,
                color: 'rgba(0,0,0,0.3)',
                size: 10,
                x: 3,
                y: 3
            }
        },
        edges: {
            smooth: {
                enabled: true,
                type: 'cubicBezier',
                forceDirection: 'vertical'
            }
        }
    };

    // Renderizar o grafo
    const network = new vis.Network(graphContainer, data, options);

    // Centralizar e ajustar zoom
    network.once('stabilizationIterationsDone', () => {
        network.fit({
            animation: {
                duration: 500,
                easingFunction: 'easeInOutQuad'
            }
        });
    });

    // Adicionar evento de clique nos nós
    network.on('click', function(params) {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const node = graphData.nodes.find(n => n.id === nodeId);
            if (node) {
                showNodeDetails(node);
            }
        }
    });
};

function createLegend() {
    const legendDiv = document.createElement('div');
    legendDiv.className = 'graph-legend';
    legendDiv.innerHTML = `
        <div class="legend-item">
            <div class="legend-color scan"></div>
            <span>📊 Scan (Tabelas)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color projection"></div>
            <span>π Projeção</span>
        </div>
        <div class="legend-item">
            <div class="legend-color selection"></div>
            <span>σ Seleção</span>
        </div>
        <div class="legend-item">
            <div class="legend-color join"></div>
            <span>⋈ Junção</span>
        </div>
        <div class="legend-item">
            <div class="legend-color cross"></div>
            <span>× Produto Cartesiano</span>
        </div>
    `;
    return legendDiv;
}

function getNodeColor(type) {
    const colorMap = {
        'SCAN': {
            background: '#4CAF50',
            border: '#388E3C',
            highlight: {
                background: '#66BB6A',
                border: '#2E7D32'
            }
        },
        'PROJECTION': {
            background: '#2196F3',
            border: '#1976D2',
            highlight: {
                background: '#42A5F5',
                border: '#1565C0'
            }
        },
        'SELECTION': {
            background: '#FF9800',
            border: '#F57C00',
            highlight: {
                background: '#FFB74D',
                border: '#E65100'
            }
        },
        'JOIN': {
            background: '#9C27B0',
            border: '#7B1FA2',
            highlight: {
                background: '#BA68C8',
                border: '#6A1B9A'
            }
        },
        'CROSS_PRODUCT': {
            background: '#F44336',
            border: '#D32F2F',
            highlight: {
                background: '#EF5350',
                border: '#C62828'
            }
        }
    };
    
    return colorMap[type] || {
        background: '#757575',
        border: '#616161',
        highlight: {
            background: '#9E9E9E',
            border: '#424242'
        }
    };
}

function getNodeShape(type) {
    const shapeMap = {
        'SCAN': 'box',
        'PROJECTION': 'ellipse',
        'SELECTION': 'diamond',
        'JOIN': 'ellipse',
        'CROSS_PRODUCT': 'ellipse'
    };
    
    return shapeMap[type] || 'box';
}

function formatNodeLabel(node) {
    switch(node.type) {
        case 'SCAN':
            return `📊 ${node.label}`;
        case 'PROJECTION':
            return `π\n${truncateText(node.details.attributes, 30)}`;
        case 'SELECTION':
            return `σ\n${truncateText(node.details.condition, 30)}`;
        case 'JOIN':
            return `⋈\n${truncateText(node.details.condition, 30)}`;
        case 'CROSS_PRODUCT':
            return '×';
        default:
            return node.label;
    }
}

function getNodeTooltip(node) {
    switch(node.type) {
        case 'SCAN':
            let scanInfo = `<b>SCAN</b><br>Tabela: ${node.details.table}`;
            if (node.details.alias) {
                scanInfo += `<br>Alias: ${node.details.alias}`;
            }
            return scanInfo;
        case 'PROJECTION':
            return `<b>PROJEÇÃO (π)</b><br>Atributos: ${node.details.attributes}`;
        case 'SELECTION':
            return `<b>SELEÇÃO (σ)</b><br>Condição: ${node.details.condition}`;
        case 'JOIN':
            return `<b>JUNÇÃO (⋈)</b><br>Condição: ${node.details.condition}`;
        case 'CROSS_PRODUCT':
            return `<b>PRODUTO CARTESIANO (×)</b><br>${node.details.left} × ${node.details.right}`;
        default:
            return node.label;
    }
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength - 3) + '...';
}

function showNodeDetails(node) {
    // Criar modal para exibir detalhes do nó
    let modal = document.getElementById('nodeDetailsModal');
    
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'nodeDetailsModal';
        modal.className = 'node-modal';
        modal.innerHTML = `
            <div class="node-modal-content">
                <span class="node-modal-close">&times;</span>
                <div id="nodeDetailsBody"></div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Fechar modal ao clicar no X
        modal.querySelector('.node-modal-close').onclick = function() {
            modal.style.display = 'none';
        };
        
        // Fechar modal ao clicar fora
        window.onclick = function(event) {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        };
    }
    
    const body = modal.querySelector('#nodeDetailsBody');
    body.innerHTML = `
        <h2>${getNodeTypeName(node.type)}</h2>
        <div class="node-details-content">
            ${formatNodeDetails(node)}
        </div>
    `;
    
    modal.style.display = 'block';
}

function getNodeTypeName(type) {
    const names = {
        'SCAN': '📊 Scan de Tabela',
        'PROJECTION': 'π Projeção',
        'SELECTION': 'σ Seleção',
        'JOIN': '⋈ Junção',
        'CROSS_PRODUCT': '× Produto Cartesiano'
    };
    return names[type] || type;
}

function formatNodeDetails(node) {
    let html = '<ul>';
    
    html += `<li><strong>Tipo:</strong> ${node.type}</li>`;
    html += `<li><strong>ID do Nó:</strong> ${node.id}</li>`;
    
    if (node.details) {
        for (const [key, value] of Object.entries(node.details)) {
            if (value !== null && value !== undefined) {
                const label = key.charAt(0).toUpperCase() + key.slice(1);
                html += `<li><strong>${label}:</strong> ${value}</li>`;
            }
        }
    }
    
    html += '</ul>';
    return html;
}
