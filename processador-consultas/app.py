from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

METADATA = {
    'categoria': ['idcategoria', 'descricao'],
    'produto': ['idproduto', 'nome', 'descricao', 'preco', 'quantestoque', 'categoria_idcategoria'],
    'tipocliente': ['idtipocliente', 'descricao'],
    'cliente': ['idcliente', 'nome', 'email', 'nascimento', 'senha', 'tipocliente_idtipocliente', 'dataregistro'],
    'tipoendereco': ['idtipoendereco', 'descricao'],
    'endereco': ['idendereco', 'enderecopadrao', 'logradouro', 'numero', 'complemento', 'bairro', 
                 'cidade', 'uf', 'cep', 'tipoendereco_idtipoendereco', 'cliente_idcliente'],
    'telefone': ['numero', 'cliente_idcliente'],
    'status': ['idstatus', 'descricao'],
    'pedido': ['idpedido', 'status_idstatus', 'datapedido', 'valortotalpedido', 'cliente_idcliente'],
    'pedido_has_produto': ['idpedidoproduto', 'pedido_idpedido', 'produto_idproduto', 
                           'quantidade', 'precounitario']
}

class SQLValidator:
    """Validador de consultas SQL conforme HU1"""
    
    def __init__(self, metadata):
        self.metadata = metadata
        self.valid_keywords = ['select', 'from', 'where', 'join', 'on', 'and', 'or']
        self.valid_operators = ['=', '>', '<', '<=', '>=', '<>']
        self.table_aliases = {}
        
    def normalize_query(self, query):
        """Remove espaços extras, normaliza e converte tudo para minúsculas"""
        query = re.sub(r'\s+', ' ', query.strip())
        query = query.lower()
        return query
    
    def validate_syntax(self, query):
        """Valida a sintaxe básica da consulta SQL"""
        errors = []
        warnings = []

        if not query.startswith('select'):
            errors.append('A consulta deve começar com SELECT')
            
        if 'from' not in query:
            errors.append('A consulta deve conter a cláusula FROM')

        if query.count('(') != query.count(')'):
            errors.append('Parênteses não estão balanceados')

        # Verificação dos JOINs
        if 'join' in query:
            join_count = len(re.findall(r'\bjoin\b', query))
            on_count = len(re.findall(r'\bon\b', query))
            
            if join_count > on_count:
                errors.append('Toda cláusula JOIN deve ter uma condição ON correspondente')
            elif on_count > join_count:
                errors.append('Cláusula ON encontrada sem JOIN correspondente')
            
            # Verificar se ON vem depois de JOIN
            join_positions = [m.start() for m in re.finditer(r'\bjoin\b', query)]
            on_positions = [m.start() for m in re.finditer(r'\bon\b', query)]
            
            for join_pos in join_positions:
                # Deve haver pelo menos um ON depois deste JOIN
                if not any(on_pos > join_pos for on_pos in on_positions):
                    errors.append('JOIN sem condição ON subsequente')
        elif re.search(r'\bon\b', query) and not re.search(r'\bjoin\b', query):
            errors.append('Cláusula ON encontrada sem JOIN correspondente')
        
        # Validar operadores lógicos no WHERE
        if 'where' in query:
            where_clause = self._extract_where_clause(query)
            if where_clause:
                # Verificar AND/OR isolados ou no início/fim
                if re.search(r'\b(and|or)\s*$', where_clause, re.IGNORECASE):
                    errors.append('Operador lógico (AND/OR) incompleto no final da cláusula WHERE')
                
                if re.search(r'^\s*(and|or)\b', where_clause, re.IGNORECASE):
                    errors.append('Operador lógico (AND/OR) no início da cláusula WHERE')
                
                # Verificar operadores lógicos duplicados (AND AND, OR OR, AND OR AND, etc)
                if re.search(r'\b(and|or)\s+(and|or)\b', where_clause, re.IGNORECASE):
                    errors.append('Operadores lógicos (AND/OR) consecutivos sem condição entre eles')
                
                # Verificar se há operadores de comparação válidos
                if not re.search(r'[=<>]|<=|>=|<>', where_clause):
                    errors.append('Cláusula WHERE sem operador de comparação válido')
                
                # Verificar se há múltiplas condições sem operadores lógicos
                # Exemplo: "campo1 = 1 campo2 = 2" (faltando AND/OR)
                comparison_count = len(re.findall(r'\w+\s*[=<>]+\s*[\w\'\"]+', where_clause))
                logical_ops_count = len(re.findall(r'\b(and|or)\b', where_clause, re.IGNORECASE))
                
                # Se tem mais de uma comparação, deve ter pelo menos (n-1) operadores lógicos
                if comparison_count > 1 and logical_ops_count < comparison_count - 1:
                    errors.append('Múltiplas condições no WHERE sem operadores lógicos (AND/OR) entre elas')
                
                # Validar cada condição individualmente
                self._validate_where_conditions(where_clause, errors)
        
        # Validar condições no ON (para JOINs)
        if 'on' in query and 'join' in query:
            on_clauses = self._extract_on_clauses(query)
            for on_clause in on_clauses:
                self._validate_on_condition(on_clause, errors)
        
        # Validar operadores de comparação completos
        # Procurar por operadores seguidos de ponto-e-vírgula ou fim sem valor
        if re.search(r'[=<>]\s*;?\s*$', query):
            errors.append('Operador de comparação incompleto (sem valor após o operador)')
        
        # Verificar se há múltiplos operadores de comparação juntos
        if re.search(r'[=<>]{3,}', query):
            errors.append('Operadores de comparação inválidos ou repetidos')
            
        return errors, warnings
    
    def _extract_where_clause(self, query):
        """Extrai a cláusula WHERE da query"""
        where_match = re.search(r'where\s+(.+?)(?:$|;)', query, re.IGNORECASE)
        if where_match:
            return where_match.group(1).strip()
        return None
    
    def _validate_where_conditions(self, where_clause, errors):
        """Valida as condições individuais no WHERE"""
        # Remover parênteses para facilitar análise
        where_clean = re.sub(r'[()]', ' ', where_clause)
        
        # Dividir por AND e OR para pegar cada condição
        conditions = re.split(r'\b(and|or)\b', where_clean, flags=re.IGNORECASE)
        
        for i, part in enumerate(conditions):
            part = part.strip()
            # Pular os próprios operadores AND/OR
            if part.lower() in ['and', 'or', '']:
                continue
            
            # Verificar se a condição tem um operador de comparação
            has_operator = re.search(r'[=<>]|<=|>=|<>', part)
            
            if has_operator:
                # Verificar se há algo antes e depois do operador
                # Padrão esperado: atributo operador valor
                # Exemplo: cliente.nome = 'joão' ou idcliente > 1
                
                # Verificar operador sem valor à direita
                if re.search(r'[=<>]+\s*$', part):
                    errors.append(f"Condição incompleta: operador sem valor à direita")
                    continue
                
                # Verificar operador sem atributo à esquerda  
                if re.search(r'^\s*[=<>]', part):
                    errors.append(f"Condição incompleta: operador sem atributo à esquerda")
                    continue
                
                # Verificar padrão completo: algo operador algo
                # Deve ter pelo menos: palavra/ponto operador palavra/número/string
                pattern = r'[\w.]+\s*(?:=|<>|<=|>=|<|>)\s*[\w.\'\"-]+'
                if not re.search(pattern, part):
                    # Pode ser que tenha operador mas falta valor ou atributo
                    if '=' in part or '<' in part or '>' in part:
                        errors.append(f"Condição malformada no WHERE")
            else:
                # Condição sem operador de comparação
                # Pode ser um erro, a menos que seja uma subcondição válida
                if part and not part.isspace():
                    # Verificar se não é apenas espaços em branco
                    if len(part.strip()) > 0:
                        errors.append(f"Condição sem operador de comparação no WHERE")
    
    def _validate_on_condition(self, on_clause, errors):
        """Valida a condição de um JOIN ON"""
        on_clause = on_clause.strip()
        
        if not on_clause:
            return
        
        # Deve ter um operador de comparação (geralmente =)
        if not re.search(r'[=<>]|<=|>=|<>', on_clause):
            errors.append(f"Cláusula ON sem operador de comparação")
            return
        
        # Verificar operador sem valor à direita
        if re.search(r'[=<>]+\s*$', on_clause):
            errors.append(f"Cláusula ON incompleta: operador sem valor à direita")
            return
        
        # Verificar operador sem atributo à esquerda
        if re.search(r'^\s*[=<>]', on_clause):
            errors.append(f"Cláusula ON incompleta: operador sem atributo à esquerda")
            return
        
        # Verificar padrão completo: tabela.campo = tabela.campo
        if not re.search(r'[\w.]+\s*=\s*[\w.]+', on_clause):
            errors.append(f"Cláusula ON malformada")
    
    def _extract_on_clauses(self, query):
        """Extrai todas as cláusulas ON da query"""
        on_clauses = []
        # Padrão: ON ... (até encontrar WHERE, outro JOIN, ou fim)
        on_matches = re.finditer(r'on\s+(.+?)(?:\s+where|\s+join|$)', query, re.IGNORECASE)
        for match in on_matches:
            on_clauses.append(match.group(1).strip())
        return on_clauses
    
    def extract_tables(self, query):
        """Extrai as tabelas da consulta (FROM e JOIN) - mantido para compatibilidade"""
        return self.extract_tables_and_aliases(query)
    
    def extract_tables_and_aliases(self, query):
        """Extrai as tabelas e seus aliases da consulta (FROM e JOIN)"""
        tables = []
        self.table_aliases = {}
        
        # Extrair tabelas do FROM - suporta alias
        # Padrão: FROM Tabela [alias] ou FROM Tabela alias
        from_pattern = r'from\s+([\w\s,]+?)(?:\s+where|\s+join|$)'
        from_match = re.search(from_pattern, query, re.IGNORECASE)
        
        if from_match:
            table_list = from_match.group(1)
            for table_expr in table_list.split(','):
                table_expr = table_expr.strip()
                # Dividir em partes (pode ser "Tabela alias" ou só "Tabela")
                parts = table_expr.split()
                if len(parts) >= 2:
                    table_name = parts[0]
                    alias = parts[1]
                    tables.append(table_name)
                    self.table_aliases[alias] = table_name
                elif len(parts) == 1:
                    table_name = parts[0]
                    tables.append(table_name)
        
        # Extrair tabelas dos JOINs - suporta alias
        # Padrão: JOIN Tabela [alias] ON
        join_pattern = r'join\s+([\w]+)(?:\s+(\w+))?\s+on'
        join_matches = re.finditer(join_pattern, query, re.IGNORECASE)
        
        for match in join_matches:
            table_name = match.group(1)
            alias = match.group(2)
            tables.append(table_name)
            if alias:
                self.table_aliases[alias] = table_name
            
        return list(set(tables))
    
    def validate_tables(self, tables):
        """Valida se as tabelas existem no modelo"""
        errors = []
        
        for table in tables:
            if table not in self.metadata:
                errors.append(f"Tabela '{table}' não existe no modelo")
                
        return errors
    
    def extract_attributes(self, query):
        """Extrai os atributos da cláusula SELECT e WHERE"""
        attributes = []
        
        select_pattern = r'select\s+(.*?)\s+from'
        select_match = re.search(select_pattern, query, re.IGNORECASE)
        
        if select_match:
            select_clause = select_match.group(1)
            if select_clause.strip() != '*':
                for attr in select_clause.split(','):
                    attr = re.sub(r'\s+as\s+\w+', '', attr, flags=re.IGNORECASE)
                    attr = attr.strip()
                    if '.' in attr:
                        attributes.append(attr)
        
        where_pattern = r'where\s+(.*?)(?:$|\s+order|\s+group)'
        where_match = re.search(where_pattern, query, re.IGNORECASE)
        
        if where_match:
            where_clause = where_match.group(1)
            attr_pattern = r'(\w+\.\w+)'
            attr_matches = re.finditer(attr_pattern, where_clause)
            for match in attr_matches:
                attributes.append(match.group(1))
        
        on_pattern = r'on\s+([\w.]+)\s*=\s*([\w.]+)'
        on_matches = re.finditer(on_pattern, query, re.IGNORECASE)
        
        for match in on_matches:
            attributes.append(match.group(1))
            attributes.append(match.group(2))
            
        return attributes
    
    def resolve_table_name(self, table_or_alias):
        """Resolve um alias para o nome real da tabela, ou retorna o próprio nome se não for alias"""
        if table_or_alias in self.table_aliases:
            return self.table_aliases[table_or_alias]
        return table_or_alias
    
    def validate_attributes(self, attributes):
        """Valida se os atributos existem nas tabelas"""
        errors = []
        
        for attr in attributes:
            if '.' in attr:
                table_or_alias, field = attr.split('.')
                table = self.resolve_table_name(table_or_alias)
                
                if table in self.metadata:
                    if field not in self.metadata[table]:
                        errors.append(f"Atributo '{field}' não existe na tabela '{table}'")
                else:
                    errors.append(f"Tabela '{table}' não encontrada para validar atributo '{field}'")
                    
        return errors
    
    def validate_operators(self, query):
        """Valida se os operadores são válidos"""
        errors = []
        
        operator_pattern = r'[=<>!]+|and|or'
        operators = re.findall(operator_pattern, query, re.IGNORECASE)
        
        for op in operators:
            op_lower = op.lower()
            if op_lower not in self.valid_operators and op_lower not in ['and', 'or']:
                if op not in self.valid_operators:
                    errors.append(f"Operador '{op}' não é válido")
                    
        return errors
    
    def validate(self, query):
        """Valida a consulta SQL completa"""
        normalized_query = self.normalize_query(query)
        
        all_errors = []
        all_warnings = []
        
        # 1. Validar sintaxe básica
        syntax_errors, syntax_warnings = self.validate_syntax(normalized_query)
        all_errors.extend(syntax_errors)
        all_warnings.extend(syntax_warnings)
        
        if syntax_errors:
            return {
                'valid': False,
                'errors': all_errors,
                'warnings': all_warnings,
                'query': normalized_query
            }
        
        # 2. Validar tabelas e extrair aliases
        tables = self.extract_tables_and_aliases(normalized_query)
        table_errors = self.validate_tables(tables)
        all_errors.extend(table_errors)
        
        # 3. Validar atributos (agora com suporte a aliases)
        attributes = self.extract_attributes(normalized_query)
        attr_errors = self.validate_attributes(attributes)
        all_errors.extend(attr_errors)
        
        # 4. Validar operadores
        op_errors = self.validate_operators(normalized_query)
        all_errors.extend(op_errors)
        
        return {
            'valid': len(all_errors) == 0,
            'errors': all_errors,
            'warnings': all_warnings,
            'query': normalized_query,
            'tables_found': tables,
            'attributes_found': attributes,
            'aliases': self.table_aliases
        }

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate_query():
    """Endpoint para validar consulta SQL"""
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({
            'valid': False,
            'errors': ['Consulta vazia'],
            'warnings': []
        })
    
    validator = SQLValidator(METADATA)
    result = validator.validate(query)
    
    return jsonify(result)

@app.route('/metadata')
def get_metadata():
    """Retorna os metadados do banco"""
    return jsonify(METADATA)

if __name__ == '__main__':
    app.run(debug=True, port=5000)