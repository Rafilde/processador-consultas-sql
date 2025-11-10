import unittest
from app import SQLValidator, METADATA

class TestExecutionPlan(unittest.TestCase):
    """Testes para HU5 – Plano de Execução"""

    def setUp(self):
        self.validator = SQLValidator(METADATA)

    def test_01_simple_select_plan(self):
        query = "SELECT * FROM Cliente"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        plan = result.get('execution_plan')
        self.assertIsNotNone(plan)
        # Deve ter pelo menos SCAN e PROJECTION
        types = [s['type'] for s in plan]
        self.assertIn('SCAN', types)
        self.assertIn('PROJECTION', types)
        # PROJECTION deve ocorrer depois de SCAN
        scan_idx = next(i for i,s in enumerate(plan) if s['type']=='SCAN')
        proj_idx = next(i for i,s in enumerate(plan) if s['type']=='PROJECTION')
        self.assertGreater(proj_idx, scan_idx)

    def test_02_select_where_plan(self):
        query = "SELECT Nome FROM Cliente WHERE Nome = 'João'"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        plan = result.get('execution_plan')
        types = [s['type'] for s in plan]
        # Deve seguir SCAN -> SELECTION -> PROJECTION (ordem relativa)
        self.assertIn('SCAN', types)
        self.assertIn('SELECTION', types)
        self.assertIn('PROJECTION', types)
        scan_idx = next(i for i,s in enumerate(plan) if s['type']=='SCAN')
        sel_idx = next(i for i,s in enumerate(plan) if s['type']=='SELECTION')
        proj_idx = next(i for i,s in enumerate(plan) if s['type']=='PROJECTION')
        self.assertGreater(sel_idx, scan_idx)
        self.assertGreater(proj_idx, sel_idx)

    def test_03_join_plan(self):
        query = (
            "SELECT Cliente.Nome, Pedido.DataPedido FROM Cliente "
            "JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente"
        )
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        plan = result.get('execution_plan')
        types = [s['type'] for s in plan]
        # Deve conter pelo menos 2 SCANs, 1 JOIN, 1 PROJECTION
        self.assertGreaterEqual(types.count('SCAN'), 2)
        self.assertIn('JOIN', types)
        self.assertIn('PROJECTION', types)
        # JOIN deve ocorrer depois de todas SCANs
        join_idx = next(i for i,s in enumerate(plan) if s['type']=='JOIN')
        scan_indices = [i for i,s in enumerate(plan) if s['type']=='SCAN']
        self.assertTrue(all(join_idx > si for si in scan_indices))
        # PROJECTION depois do JOIN
        proj_idx = next(i for i,s in enumerate(plan) if s['type']=='PROJECTION')
        self.assertGreater(proj_idx, join_idx)

if __name__ == '__main__':
    unittest.main()
