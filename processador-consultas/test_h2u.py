import unittest
from app import SQLValidator, METADATA

class TestRelationalAlgebra(unittest.TestCase):
    """Testes para HU2 – Conversão para Álgebra Relacional"""

    def setUp(self):
        self.validator = SQLValidator(METADATA)

    def test_01_select_all_single_table(self):
        query = "SELECT * FROM Cliente"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        ra = result.get('relational_algebra')
        self.assertIsNotNone(ra)
        # Deve conter π{*} e a relação base
        self.assertIn('π{*}', ra)
        self.assertIn('cliente', ra)

    def test_02_projection_and_where(self):
        query = "SELECT Cliente.Nome, Cliente.Email FROM Cliente WHERE Cliente.Nome = 'maria'"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        ra = result.get('relational_algebra')
        self.assertIn("π{cliente.nome, cliente.email}", ra)
        # σ deve conter a condição sem espaços ao redor do operador
        self.assertIn("σ{cliente.nome='maria'}", ra)

    def test_03_join_with_alias(self):
        query = (
            "SELECT c.Nome, p.DataPedido FROM Cliente c "
            "JOIN Pedido p ON c.idCliente = p.Cliente_idCliente "
            "WHERE c.Nome = 'maria' AND p.DataPedido >= '2024-01-01'"
        )
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        ra = result.get('relational_algebra')
        # projeção com alias
        self.assertIn("π{c.nome, p.datapedido}", ra)
        # junção com condição sem espaços
        self.assertIn("⋈{c.idcliente=p.cliente_idcliente}", ra)
        # seleção com ∧ e ≥
        self.assertIn("σ{c.nome='maria' ∧ p.datapedido≥'2024-01-01'}", ra)

    def test_04_multiple_joins(self):
        query = (
            "SELECT pr.Nome, pr.Preco FROM Cliente c "
            "JOIN Pedido p ON c.idCliente = p.Cliente_idCliente "
            "JOIN Pedido_has_Produto pp ON p.idPedido = pp.Pedido_idPedido "
            "JOIN Produto pr ON pp.Produto_idProduto = pr.idProduto"
        )
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        ra = result.get('relational_algebra')
        # Verifica encadeamento de 3 junções
        self.assertIn('⋈{c.idcliente=p.cliente_idcliente}', ra)
        self.assertIn('⋈{p.idpedido=pp.pedido_idpedido}', ra)
        self.assertIn('⋈{pp.produto_idproduto=pr.idproduto}', ra)

    def test_05_where_before_from(self):
        """WHERE antes de FROM deve ser suportado na conversão"""
        query = """
            SELECT numero 
            WHERE numero >= 200 
            FROM endereco;
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        ra = result.get('relational_algebra')
        # Formato esperado: π{numero}(σ{numero≥200}(endereco))
        self.assertIn("π{numero}(σ{numero≥200}(endereco))", ra)

if __name__ == '__main__':
    # Tenta usar o runner colorido do HU1 se disponível
    try:
        from test_h1u import ColoredTextTestRunner

        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        suite.addTests(loader.loadTestsFromTestCase(TestRelationalAlgebra))

        runner = ColoredTextTestRunner(verbosity=0)
        result = runner.run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)
    except Exception:
        # Fallback para runner padrão
        unittest.main()
