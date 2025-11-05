import unittest
import sys
from app import SQLValidator, METADATA, OperatorGraph


class TestOperatorGraph(unittest.TestCase):
    """Testes para HU3 – Construção do Grafo de Operadores"""

    def setUp(self):
        self.validator = SQLValidator(METADATA)
        self.graph_builder = OperatorGraph()

    def test_01_simple_select_graph(self):
        """[GRAFO] Grafo simples com apenas SELECT e FROM"""
        query = "SELECT * FROM Cliente"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        self.assertIn('nodes', graph)
        self.assertIn('edges', graph)
        
        # Deve ter 2 nós: SCAN (Cliente) e PROJECTION (*)
        self.assertEqual(len(graph['nodes']), 2)
        
        # Verificar tipos de nós
        node_types = [n['type'] for n in graph['nodes']]
        self.assertIn('SCAN', node_types)
        self.assertIn('PROJECTION', node_types)

    def test_02_select_with_where(self):
        """[GRAFO] Grafo com SELECT, FROM e WHERE"""
        query = "SELECT Nome FROM Cliente WHERE Nome = 'João'"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        # Deve ter 3 nós: SCAN, SELECTION, PROJECTION
        self.assertEqual(len(graph['nodes']), 3)
        
        node_types = [n['type'] for n in graph['nodes']]
        self.assertIn('SCAN', node_types)
        self.assertIn('SELECTION', node_types)
        self.assertIn('PROJECTION', node_types)
        
        # Verificar se há arestas conectando os nós
        self.assertGreater(len(graph['edges']), 0)

    def test_03_join_graph(self):
        """[GRAFO] Grafo com JOIN"""
        query = """
            SELECT Cliente.Nome, Pedido.DataPedido 
            FROM Cliente 
            JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        node_types = [n['type'] for n in graph['nodes']]
        
        # Deve ter: 2 SCANs (Cliente, Pedido), 1 JOIN, 1 PROJECTION
        self.assertEqual(node_types.count('SCAN'), 2)
        self.assertEqual(node_types.count('JOIN'), 1)
        self.assertEqual(node_types.count('PROJECTION'), 1)
        
        # Total de 4 nós
        self.assertEqual(len(graph['nodes']), 4)

    def test_04_multiple_joins_graph(self):
        """[GRAFO] Grafo com múltiplos JOINs encadeados"""
        query = """
            SELECT pr.Nome 
            FROM Cliente c 
            JOIN Pedido p ON c.idCliente = p.Cliente_idCliente 
            JOIN Pedido_has_Produto pp ON p.idPedido = pp.Pedido_idPedido
            JOIN Produto pr ON pp.Produto_idProduto = pr.idProduto
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        node_types = [n['type'] for n in graph['nodes']]
        
        # Deve ter: 4 SCANs, 3 JOINs, 1 PROJECTION
        self.assertEqual(node_types.count('SCAN'), 4)
        self.assertEqual(node_types.count('JOIN'), 3)
        self.assertEqual(node_types.count('PROJECTION'), 1)

    def test_05_join_with_where_graph(self):
        """[GRAFO] Grafo com JOIN e WHERE"""
        query = """
            SELECT c.Nome, p.DataPedido 
            FROM Cliente c 
            JOIN Pedido p ON c.idCliente = p.Cliente_idCliente 
            WHERE c.Nome = 'João' AND p.DataPedido >= '2024-01-01'
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        node_types = [n['type'] for n in graph['nodes']]
        
        # Deve ter: 2 SCANs, 1 JOIN, 1 SELECTION, 1 PROJECTION
        self.assertEqual(node_types.count('SCAN'), 2)
        self.assertEqual(node_types.count('JOIN'), 1)
        self.assertEqual(node_types.count('SELECTION'), 1)
        self.assertEqual(node_types.count('PROJECTION'), 1)

    def test_06_cross_product_graph(self):
        """[GRAFO] Grafo com produto cartesiano (múltiplas tabelas no FROM)"""
        query = "SELECT * FROM Cliente, Pedido"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        node_types = [n['type'] for n in graph['nodes']]
        
        # Deve ter: 2 SCANs, 1 CROSS_PRODUCT, 1 PROJECTION
        self.assertEqual(node_types.count('SCAN'), 2)
        self.assertEqual(node_types.count('CROSS_PRODUCT'), 1)
        self.assertEqual(node_types.count('PROJECTION'), 1)

    def test_07_root_is_projection(self):
        """[GRAFO] Raiz do grafo deve ser sempre a projeção"""
        query = "SELECT Nome FROM Cliente WHERE Nome = 'João'"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        # Verificar se existe um nó raiz
        self.assertIn('root', graph)
        root_id = graph['root']
        
        # Encontrar o nó raiz
        root_node = next((n for n in graph['nodes'] if n['id'] == root_id), None)
        self.assertIsNotNone(root_node)
        
        # Raiz deve ser PROJECTION
        self.assertEqual(root_node['type'], 'PROJECTION')

    def test_08_leaves_are_scans(self):
        """[GRAFO] Folhas do grafo devem ser sempre SCANs"""
        query = """
            SELECT c.Nome, p.DataPedido 
            FROM Cliente c 
            JOIN Pedido p ON c.idCliente = p.Cliente_idCliente
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        # Encontrar nós que não têm arestas saindo deles (folhas)
        nodes_with_outgoing_edges = set(edge['from'] for edge in graph['edges'])
        leaf_nodes = [n for n in graph['nodes'] if n['id'] not in nodes_with_outgoing_edges]
        
        # Todas as folhas devem ser SCAN
        for leaf in leaf_nodes:
            self.assertEqual(leaf['type'], 'SCAN')

    def test_09_edge_flow(self):
        """[GRAFO] Arestas devem representar fluxo correto (de baixo para cima)"""
        query = "SELECT Nome FROM Cliente WHERE Nome = 'João'"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        # Deve haver pelo menos 2 arestas (SCAN->SELECTION->PROJECTION)
        self.assertGreaterEqual(len(graph['edges']), 2)
        
        # Verificar se cada aresta tem 'from' e 'to'
        for edge in graph['edges']:
            self.assertIn('from', edge)
            self.assertIn('to', edge)
            self.assertIsInstance(edge['from'], int)
            self.assertIsInstance(edge['to'], int)

    def test_10_node_details(self):
        """[GRAFO] Nós devem conter detalhes adequados"""
        query = "SELECT Nome FROM Cliente WHERE Nome = 'João'"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        for node in graph['nodes']:
            # Cada nó deve ter id, type, label e details
            self.assertIn('id', node)
            self.assertIn('type', node)
            self.assertIn('label', node)
            self.assertIn('details', node)
            
            # Verificar detalhes específicos por tipo
            if node['type'] == 'SCAN':
                self.assertIn('table', node['details'])
            elif node['type'] == 'SELECTION':
                self.assertIn('condition', node['details'])
            elif node['type'] == 'PROJECTION':
                self.assertIn('attributes', node['details'])
            elif node['type'] == 'JOIN':
                self.assertIn('condition', node['details'])

    def test_11_aliases_in_graph(self):
        """[GRAFO] Aliases devem ser refletidos nos nós"""
        query = """
            SELECT c.Nome 
            FROM Cliente c 
            JOIN Pedido p ON c.idCliente = p.Cliente_idCliente
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        # Encontrar nós SCAN
        scan_nodes = [n for n in graph['nodes'] if n['type'] == 'SCAN']
        
        # Verificar se os aliases estão presentes
        labels = [n['label'] for n in scan_nodes]
        self.assertIn('c', labels)  # alias para Cliente
        self.assertIn('p', labels)  # alias para Pedido

    def test_12_complex_query_graph(self):
        """[GRAFO] Grafo completo de consulta complexa"""
        query = """
            SELECT pr.Nome, pr.Preco
            FROM Cliente c 
            JOIN Pedido p ON c.idCliente = p.Cliente_idCliente 
            JOIN Pedido_has_Produto pp ON p.idPedido = pp.Pedido_idPedido
            JOIN Produto pr ON pp.Produto_idProduto = pr.idProduto
            WHERE c.Nome = 'João' AND pr.Preco > 100
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        
        graph = result.get('operator_graph')
        self.assertIsNotNone(graph)
        
        # Verificar estrutura completa
        node_types = [n['type'] for n in graph['nodes']]
        
        # Deve ter todos os tipos de operadores
        self.assertIn('SCAN', node_types)
        self.assertIn('JOIN', node_types)
        self.assertIn('SELECTION', node_types)
        self.assertIn('PROJECTION', node_types)
        
        # 4 tabelas = 4 SCANs
        self.assertEqual(node_types.count('SCAN'), 4)
        
        # 3 JOINs
        self.assertEqual(node_types.count('JOIN'), 3)
        
        # 1 SELECTION
        self.assertEqual(node_types.count('SELECTION'), 1)
        
        # 1 PROJECTION
        self.assertEqual(node_types.count('PROJECTION'), 1)


if __name__ == '__main__':
    # Tenta usar o runner colorido do HU1 se disponível
    try:
        from test_h1u import ColoredTextTestRunner

        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(TestOperatorGraph))

        runner = ColoredTextTestRunner(verbosity=0)
        result = runner.run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)
    except ImportError:
        # Fallback para runner padrão
        unittest.main()
