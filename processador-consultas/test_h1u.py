import unittest
import sys
import io
from app import SQLValidator, METADATA
from datetime import datetime

class Colors:
    """Códigos de cores ANSI para terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Imprime cabeçalho estilizado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

def print_section(text):
    """Imprime seção estilizada"""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}▶ {text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'─' * 70}{Colors.ENDC}")

class ColoredTextTestResult(unittest.TextTestResult):
    """Resultado de teste customizado com cores e formatação"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []
        self.current_test_class = None
        self.last_category = None
        
    def startTest(self, test):
        """Inicia um teste e exibe cabeçalho da classe se necessário"""
        super().startTest(test)
        self.current_test_start = datetime.now()
        
        test_class = test.__class__.__name__
        if test_class != self.current_test_class:
            self.current_test_class = test_class
            self._print_class_header(test_class)
            self.last_category = None
    
    def _print_class_header(self, test_class):
        """Imprime cabeçalho da classe de teste"""
        headers = {
            'TestSQLValidator': 'TESTES DO VALIDADOR SQL',
            'TestMetadata': 'TESTES DE METADADOS'
        }
        
        if test_class in headers:
            title = headers[test_class]
            padding = ' ' * (68 - len(title) - 2)
            print(f"\n{Colors.OKBLUE}{'┌' + '─' * 68 + '┐'}{Colors.ENDC}")
            print(f"{Colors.OKBLUE}│{Colors.BOLD}  {title}{padding}│{Colors.ENDC}")
            print(f"{Colors.OKBLUE}{'└' + '─' * 68 + '┘'}{Colors.ENDC}\n")
    
    def _extract_category(self, description):
        """Extrai a categoria da descrição (texto entre [])"""
        if '[' in description and ']' in description:
            start = description.find('[')
            end = description.find(']')
            return description[start+1:end]
        return None
    
    def _print_category_separator(self, category):
        """Imprime linha em branco ao mudar de categoria"""
        if category and category != self.last_category:
            if self.last_category is not None:
                print()
            self.last_category = category
    
    def _add_result(self, test, status, duration):
        """Adiciona resultado e imprime linha formatada"""
        description = test.shortDescription() or str(test)
        category = self._extract_category(description)
        self._print_category_separator(category)
        
        self.test_results.append({
            'name': description,
            'status': status,
            'duration': duration
        })
        
        symbols = {
            'PASS': (f"{Colors.OKGREEN}✓{Colors.ENDC}", Colors.OKGREEN),
            'FAIL': (f"{Colors.FAIL}✗{Colors.ENDC}", Colors.FAIL),
            'ERROR': (f"{Colors.FAIL}✗{Colors.ENDC}", Colors.FAIL),
            'SKIP': (f"{Colors.WARNING}⊘{Colors.ENDC}", Colors.WARNING)
        }
        
        symbol, color = symbols.get(status, ('', ''))
        status_text = f"[{status} - {duration:.3f}s]" if status != 'PASS' else f"[{duration:.3f}s]"
        
        print(f"  {symbol} {description:<65} {color}{status_text}{Colors.ENDC}")
        
    def addSuccess(self, test):
        super().addSuccess(test)
        duration = (datetime.now() - self.current_test_start).total_seconds()
        self._add_result(test, 'PASS', duration)
        
    def addError(self, test, err):
        super().addError(test, err)
        duration = (datetime.now() - self.current_test_start).total_seconds()
        self._add_result(test, 'ERROR', duration)
        
    def addFailure(self, test, err):
        super().addFailure(test, err)
        duration = (datetime.now() - self.current_test_start).total_seconds()
        self._add_result(test, 'FAIL', duration)
        
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        duration = (datetime.now() - self.current_test_start).total_seconds()
        self._add_result(test, 'SKIP', duration)

class ColoredTextTestRunner(unittest.TextTestRunner):
    """Runner customizado com cores"""
    resultclass = ColoredTextTestResult
    
    def run(self, test):
        """Executa os testes e exibe resultados"""
        print_header("EXECUTANDO TESTES - VALIDADOR SQL")
        
        result = self.resultclass(io.StringIO(), self.descriptions, self.verbosity)
        result.failfast = self.failfast
        result.buffer = self.buffer
        
        test(result)
        self._print_summary(result)
        
        return result
    
    def _print_summary(self, result):
        """Imprime resumo dos testes"""
        print_section("RESUMO DOS TESTES")
        
        total = result.testsRun
        passed = total - len(result.failures) - len(result.errors)
        failed = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        total_time = sum(r['duration'] for r in result.test_results)
        
        print(f"\n{Colors.BOLD}Estatísticas:{Colors.ENDC}")
        print(f"  Total de testes:  {Colors.BOLD}{total}{Colors.ENDC}")
        print(f"  {Colors.OKGREEN}✓ Aprovados:{Colors.ENDC}      {Colors.OKGREEN}{passed}{Colors.ENDC}")
        
        if failed > 0:
            print(f"  {Colors.FAIL}✗ Falharam:{Colors.ENDC}       {Colors.FAIL}{failed}{Colors.ENDC}")
        if errors > 0:
            print(f"  {Colors.FAIL}✗ Erros:{Colors.ENDC}          {Colors.FAIL}{errors}{Colors.ENDC}")
        if skipped > 0:
            print(f"  {Colors.WARNING}⊘ Ignorados:{Colors.ENDC}      {Colors.WARNING}{skipped}{Colors.ENDC}")
        
        print(f"  {Colors.OKCYAN}⏱ Tempo total:{Colors.ENDC}    {Colors.OKCYAN}{total_time:.3f}s{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}{'─' * 70}{Colors.ENDC}")
        if result.wasSuccessful():
            print(f"{Colors.OKGREEN}{Colors.BOLD}✓ TODOS OS TESTES PASSARAM! 🎉{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}✗ ALGUNS TESTES FALHARAM{Colors.ENDC}")
        print(f"{Colors.BOLD}{'─' * 70}{Colors.ENDC}\n")
        
        if failed > 0 or errors > 0:
            self._print_failure_details(result)
    
    def _print_failure_details(self, result):
        """Imprime detalhes das falhas e erros"""
        print_section("DETALHES DAS FALHAS")
        
        for test, traceback in result.failures + result.errors:
            print(f"\n{Colors.FAIL}✗ {test}{Colors.ENDC}")
            print(f"{Colors.FAIL}{traceback}{Colors.ENDC}")

class TestSQLValidator(unittest.TestCase):
    """Testes unitários para o validador SQL - HU1"""
    
    def setUp(self):
        """Configuração inicial para cada teste"""
        self.validator = SQLValidator(METADATA)
    
    # ==================== SINTAXE BÁSICA ====================
    
    def test_01_consulta_valida_simples(self):
        """[SINTAXE] Consulta SELECT simples válida"""
        query = "SELECT * FROM Cliente"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
    
    def test_02_consulta_sem_select(self):
        """[SINTAXE] Consulta que não começa com SELECT"""
        query = "FROM Cliente"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertIn('A consulta deve começar com SELECT', result['errors'])
    
    def test_03_consulta_sem_from(self):
        """[SINTAXE] Consulta sem cláusula FROM"""
        query = "SELECT Nome"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertIn('A consulta deve conter a cláusula FROM', result['errors'])
    
    def test_04_consulta_vazia(self):
        """[SINTAXE] Consulta vazia"""
        result = self.validator.validate("")
        self.assertFalse(result['valid'])
    
    # ==================== NORMALIZAÇÃO ====================
    
    def test_05_normalizacao_espacos_extras(self):
        """[NORMALIZAÇÃO] Remove espaços extras corretamente"""
        query = "SELECT   *   FROM    Cliente"
        result = self.validator.validate(query)
        self.assertEqual(result['query'], "select * from cliente")
    
    def test_06_case_insensitive(self):
        """[NORMALIZAÇÃO] Ignora maiúsculas/minúsculas"""
        queries = ["SELECT * FROM Cliente", "select * from cliente", "SeLeCt * FrOm ClIeNtE"]
        for query in queries:
            result = self.validator.validate(query)
            self.assertNotIn('A consulta deve começar com SELECT', result['errors'])
    
    # ==================== TABELAS ====================
    
    def test_07_tabela_existente(self):
        """[TABELAS] Validação com tabela existente"""
        query = "SELECT * FROM Cliente"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        self.assertIn('cliente', result['tables_found'])
    
    def test_08_tabela_inexistente(self):
        """[TABELAS] Validação com tabela inexistente"""
        query = "SELECT * FROM Funcionario"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('funcionario' in error.lower() for error in result['errors']))
    
    def test_09_multiplas_tabelas_from(self):
        """[TABELAS] Múltiplas tabelas na cláusula FROM"""
        query = "SELECT * FROM Cliente, Pedido"
        result = self.validator.validate(query)
        self.assertIn('cliente', result['tables_found'])
        self.assertIn('pedido', result['tables_found'])
    
    # ==================== ATRIBUTOS ====================
    
    def test_10_atributo_valido(self):
        """[ATRIBUTOS] Atributo válido na tabela"""
        query = "SELECT Cliente.Nome FROM Cliente"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
    
    def test_11_atributo_invalido(self):
        """[ATRIBUTOS] Atributo que não existe na tabela"""
        query = "SELECT Cliente.CPF FROM Cliente"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('cpf' in error.lower() for error in result['errors']))
    
    def test_12_multiplos_atributos(self):
        """[ATRIBUTOS] Múltiplos atributos no SELECT"""
        query = "SELECT Cliente.Nome, Cliente.Email FROM Cliente"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
    
    # ==================== WHERE ====================
    
    def test_13_where_com_operador_igual(self):
        """[WHERE] WHERE com operador ="""
        query = "SELECT * FROM Cliente WHERE Cliente.Nome = 'João'"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
    
    def test_14_where_com_operadores_comparacao(self):
        """[WHERE] WHERE com operadores de comparação"""
        queries = [
            "SELECT * FROM Produto WHERE Produto.Preco > 100",
            "SELECT * FROM Produto WHERE Produto.Preco < 50",
            "SELECT * FROM Produto WHERE Produto.Preco >= 100",
            "SELECT * FROM Produto WHERE Produto.Preco <= 50",
            "SELECT * FROM Produto WHERE Produto.Preco <> 0"
        ]
        for query in queries:
            result = self.validator.validate(query)
            self.assertTrue(result['valid'], f"Falhou para: {query}")
    
    def test_15_where_com_and(self):
        """[WHERE] WHERE com operador AND"""
        query = "SELECT * FROM Produto WHERE Produto.Preco > 100 AND Produto.QuantEstoque > 0"
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
    
    # ==================== JOIN ====================
    
    def test_16_join_simples(self):
        """[JOIN] JOIN simples"""
        query = """
            SELECT Cliente.Nome, Pedido.DataPedido 
            FROM Cliente 
            JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        self.assertIn('cliente', result['tables_found'])
        self.assertIn('pedido', result['tables_found'])
    
    def test_17_multiplos_joins(self):
        """[JOIN] Múltiplos JOINs"""
        query = """
            SELECT c.Nome, p.DataPedido, pr.Nome
            FROM Cliente c
            JOIN Pedido p ON c.idCliente = p.Cliente_idCliente
            JOIN Pedido_has_Produto pp ON p.idPedido = pp.Pedido_idPedido
            JOIN Produto pr ON pp.Produto_idProduto = pr.idProduto
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['tables_found']), 4)
    
    def test_18_join_tabela_inexistente(self):
        """[JOIN] JOIN com tabela inexistente"""
        query = """
            SELECT * 
            FROM Cliente 
            JOIN Funcionario ON Cliente.idCliente = Funcionario.Cliente_id
        """
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('funcionario' in error.lower() for error in result['errors']))
    
    # ==================== PARÊNTESES ====================
    
    def test_19_parenteses_balanceados(self):
        """[PARÊNTESES] Parênteses balanceados"""
        query = "SELECT * FROM Cliente WHERE (Cliente.Nome = 'João' AND Cliente.Email = 'joao@email.com')"
        result = self.validator.validate(query)
        self.assertNotIn('Parênteses não estão balanceados', result['errors'])
    
    def test_20_parenteses_desbalanceados(self):
        """[PARÊNTESES] Parênteses desbalanceados"""
        queries = [
            "SELECT * FROM Cliente WHERE (Cliente.Nome = 'João'",
            "SELECT * FROM Cliente WHERE Cliente.Nome = 'João')",
            "SELECT * FROM Cliente WHERE ((Cliente.Nome = 'João')"
        ]
        for query in queries:
            result = self.validator.validate(query)
            self.assertFalse(result['valid'])
            self.assertIn('Parênteses não estão balanceados', result['errors'])
    
    # ==================== VALIDAÇÃO AVANÇADA DE SINTAXE ====================
    
    def test_21_join_sem_on(self):
        """[SINTAXE AVANÇADA] JOIN sem cláusula ON"""
        query = "SELECT * FROM Cliente JOIN Pedido WHERE Cliente.Nome = 'João'"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('join' in error.lower() and 'on' in error.lower() for error in result['errors']))
    
    def test_22_on_sem_join(self):
        """[SINTAXE AVANÇADA] ON sem JOIN"""
        query = "SELECT * FROM Cliente ON Cliente.idCliente = 1"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('on' in error.lower() for error in result['errors']))
    
    def test_23_and_no_final_where(self):
        """[SINTAXE AVANÇADA] AND no final da cláusula WHERE"""
        query = "SELECT * FROM Cliente WHERE Cliente.Nome = 'João' AND"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('and' in error.lower() or 'or' in error.lower() for error in result['errors']))
    
    def test_24_or_no_final_where(self):
        """[SINTAXE AVANÇADA] OR no final da cláusula WHERE"""
        query = "SELECT * FROM Cliente WHERE Cliente.Email = 'test@email.com' OR"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('and' in error.lower() or 'or' in error.lower() for error in result['errors']))
    
    def test_25_and_no_inicio_where(self):
        """[SINTAXE AVANÇADA] AND no início da cláusula WHERE"""
        query = "SELECT * FROM Cliente WHERE AND Cliente.Nome = 'João'"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('and' in error.lower() or 'or' in error.lower() for error in result['errors']))
    
    def test_26_operadores_logicos_consecutivos(self):
        """[SINTAXE AVANÇADA] Operadores lógicos consecutivos"""
        queries = [
            "SELECT * FROM Cliente WHERE Cliente.Nome = 'João' AND AND Cliente.Email = 'joao@email.com'",
            "SELECT * FROM Cliente WHERE Cliente.Nome = 'João' OR OR Cliente.Email = 'joao@email.com'",
            "SELECT * FROM Cliente WHERE Cliente.Nome = 'João' AND OR Cliente.Email = 'joao@email.com'"
        ]
        for query in queries:
            result = self.validator.validate(query)
            self.assertFalse(result['valid'], f"Deveria falhar para: {query}")
            self.assertTrue(any('consecutivos' in error.lower() or 'operador' in error.lower() for error in result['errors']))
    
    def test_27_where_sem_comparacao(self):
        """[SINTAXE AVANÇADA] WHERE sem operador de comparação"""
        query = "SELECT * FROM Cliente WHERE Cliente.Nome"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('comparação' in error.lower() for error in result['errors']))
    
    def test_28_operador_incompleto(self):
        """[SINTAXE AVANÇADA] Operador de comparação incompleto"""
        query = "SELECT * FROM Cliente WHERE Cliente.idCliente ="
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('incompleto' in error.lower() for error in result['errors']))
    
    def test_29_consulta_complexa_com_erro_and(self):
        """[SINTAXE AVANÇADA] Consulta complexa sem AND"""
        query = """
            SELECT cliente.nome, pedido.idPedido, pedido.DataPedido, pedido.ValorTotalPedido
            FROM Cliente JOIN pedido ON cliente.idcliente = pedido.Cliente_idCliente
            WHERE cliente.TipoCliente_idTipoCliente = 1 pedido.ValorTotalPedido = 0
        """
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        # Deve detectar que faltam operadores lógicos entre as condições
    
    def test_30_join_multiplos_sem_on(self):
        """[SINTAXE AVANÇADA] Múltiplos JOINs com ON faltando"""
        query = """
            SELECT * FROM Cliente 
            JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente
            JOIN Produto
        """
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('join' in error.lower() and 'on' in error.lower() for error in result['errors']))
    
    def test_31_where_sem_operador_igual(self):
        """[VALIDAÇÃO DETALHADA] WHERE sem operador = """
        query = "SELECT * FROM Cliente WHERE Cliente.idCliente 1"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('comparação' in error.lower() for error in result['errors']))
    
    def test_32_where_operador_sem_valor(self):
        """[VALIDAÇÃO DETALHADA] WHERE com operador mas sem valor"""
        query = "SELECT * FROM Cliente WHERE Cliente.idCliente ="
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('incompleta' in error.lower() or 'valor' in error.lower() for error in result['errors']))
    
    def test_33_where_operador_sem_atributo(self):
        """[VALIDAÇÃO DETALHADA] WHERE com operador mas sem atributo"""
        query = "SELECT * FROM Cliente WHERE = 1"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('atributo' in error.lower() or 'esquerda' in error.lower() for error in result['errors']))
    
    def test_34_on_sem_operador(self):
        """[VALIDAÇÃO DETALHADA] ON sem operador de comparação"""
        query = "SELECT * FROM Cliente JOIN Pedido ON Cliente.idCliente Pedido.Cliente_idCliente"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('on' in error.lower() and 'operador' in error.lower() for error in result['errors']))
    
    def test_35_on_operador_sem_valor(self):
        """[VALIDAÇÃO DETALHADA] ON com operador mas sem valor"""
        query = "SELECT * FROM Cliente JOIN Pedido ON Cliente.idCliente = WHERE Cliente.Nome = 'João'"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('on' in error.lower() and ('incompleta' in error.lower() or 'direita' in error.lower()) for error in result['errors']))
    
    def test_36_multiplas_condicoes_where_incompletas(self):
        """[VALIDAÇÃO DETALHADA] Múltiplas condições WHERE com erros"""
        query = "SELECT * FROM Cliente WHERE idCliente = 1 AND Nome"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        self.assertTrue(any('comparação' in error.lower() for error in result['errors']))
    
    def test_37_where_com_comparacao_malformada(self):
        """[VALIDAÇÃO DETALHADA] WHERE com comparação malformada"""
        query = "SELECT * FROM Cliente WHERE Cliente.idCliente 1 AND Cliente.Nome = 'João'"
        result = self.validator.validate(query)
        self.assertFalse(result['valid'])
        # Deve detectar condição sem operador ou malformada
    
    # ==================== CASOS COMPLEXOS ====================
    
    def test_38_consulta_complexa_valida(self):
        """[COMPLEXO] Consulta complexa e válida"""
        query = """
            SELECT c.Nome, c.Email, p.DataPedido, pr.Nome, pr.Preco
            FROM Cliente c
            JOIN Pedido p ON c.idCliente = p.Cliente_idCliente
            JOIN Pedido_has_Produto pp ON p.idPedido = pp.Pedido_idPedido
            JOIN Produto pr ON pp.Produto_idProduto = pr.idProduto
            WHERE c.Nome = 'Maria' AND pr.Preco > 50
        """
        result = self.validator.validate(query)
        self.assertTrue(result['valid'], f"Erros: {result['errors']}")
    
    def test_39_alias_em_tabelas(self):
        """[COMPLEXO] Uso de alias em tabelas"""
        query = "SELECT c.Nome FROM Cliente c"
        result = self.validator.validate(query)
        self.assertNotIn('A consulta deve conter a cláusula FROM', result['errors'])
    
    # ==================== EXTRAÇÃO ====================
    
    def test_40_extracao_tabelas(self):
        """[EXTRAÇÃO] Extração correta de tabelas"""
        query = "SELECT * FROM Cliente JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente"
        tables = self.validator.extract_tables(query.lower())
        self.assertIn('cliente', tables)
        self.assertIn('pedido', tables)
        self.assertEqual(len(tables), 2)
    
    def test_41_extracao_atributos_select(self):
        """[EXTRAÇÃO] Extração de atributos do SELECT"""
        query = "SELECT Cliente.Nome, Cliente.Email FROM Cliente"
        normalized = self.validator.normalize_query(query)
        attributes = self.validator.extract_attributes(normalized)
        self.assertIn('cliente.nome', attributes)
        self.assertIn('cliente.email', attributes)
    
    def test_42_extracao_atributos_where(self):
        """[EXTRAÇÃO] Extração de atributos do WHERE"""
        query = "SELECT * FROM Cliente WHERE Cliente.Nome = 'João'"
        normalized = self.validator.normalize_query(query)
        attributes = self.validator.extract_attributes(normalized)
        self.assertIn('cliente.nome', attributes)

class TestMetadata(unittest.TestCase):
    """Testes para verificar integridade dos metadados"""
    
    def test_43_todas_tabelas_presentes(self):
        """[METADATA] Todas as tabelas esperadas estão presentes"""
        expected_tables = [
            'categoria', 'produto', 'tipocliente', 'cliente',
            'tipoendereco', 'endereco', 'telefone', 'status',
            'pedido', 'pedido_has_produto'
        ]
        for table in expected_tables:
            self.assertIn(table, METADATA)
    
    def test_44_tabelas_tem_campos(self):
        """[METADATA] Todas as tabelas têm campos definidas"""
        for table, fields in METADATA.items():
            self.assertIsInstance(fields, list)
            self.assertGreater(len(fields), 0, f"Tabela {table} não tem campos")
    
    def test_45_cliente_campos_corretos(self):
        """[METADATA] Cliente tem os campos corretos"""
        expected_fields = [
            'idcliente', 'nome', 'email', 'nascimento', 
            'senha', 'tipocliente_idtipocliente', 'dataregistro'
        ]
        for field in expected_fields:
            self.assertIn(field, METADATA['cliente'])

def run_tests():
    """Executa todos os testes"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestSQLValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestMetadata))
    
    runner = ColoredTextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)