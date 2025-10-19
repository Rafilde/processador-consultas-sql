from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

METADATA = {
    'Categoria': ['idCategoria', 'Descricao'],
    'Produto': ['idProduto', 'Nome', 'Descricao', 'Preco', 'QuantEstoque', 'Categoria_idCategoria'],
    'TipoCliente': ['idTipoCliente', 'Descricao'],
    'Cliente': ['idCliente', 'Nome', 'Email', 'Nascimento', 'Senha', 'TipoCliente_idTipoCliente', 'DataRegistro'],
    'TipoEndereco': ['idTipoEndereco', 'Descricao'],
    'Endereco': ['idEndereco', 'EnderecoPadrao', 'Logradouro', 'Numero', 'Complemento', 'Bairro', 
                 'Cidade', 'UF', 'CEP', 'TipoEndereco_idTipoEndereco', 'Cliente_idCliente'],
    'Telefone': ['Numero', 'Cliente_idCliente'],
    'Status': ['idStatus', 'Descricao'],
    'Pedido': ['idPedido', 'Status_idStatus', 'DataPedido', 'ValorTotalPedido', 'Cliente_idCliente'],
    'Pedido_has_Produto': ['idPedidoProduto', 'Pedido_idPedido', 'Produto_idProduto', 
                           'Quantidade', 'PrecoUnitario']
}

class SQLValidator:
    """Validador de consultas SQL conforme HU1"""
    
    def __init__(self, metadata):
        self.metadata = metadata
        self.valid_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'AND', 'OR']
        self.valid_operators = ['=', '>', '<', '<=', '>=', '<>']
        self.table_aliases = {}
        
    def normalize_query(self, query):
        """Remove espaços extras e normaliza a query"""
        query = re.sub(r'\s+', ' ', query.strip())
        return query
    
    def validate_syntax(self, query):
        """Valida a sintaxe básica da consulta SQL"""
        errors = []
        warnings = []
        
        query_upper = query.upper()
        
        if not query_upper.startswith('SELECT'):
            errors.append('A consulta deve começar com SELECT')
            
        if 'FROM' not in query_upper:
            errors.append('A consulta deve conter a cláusula FROM')

        if query.count('(') != query.count(')'):
            errors.append('Parênteses não estão balanceados')
            
        return errors, warnings
    
    def extract_tables(self, query):
        """Extrai as tabelas da consulta (FROM e JOIN) - mantido para compatibilidade"""
        return self.extract_tables_and_aliases(query)
    
    def extract_tables_and_aliases(self, query):
        """Extrai as tabelas e seus aliases da consulta (FROM e JOIN)"""
        tables = []
        self.table_aliases = {}
        
        # Extrair tabelas do FROM - suporta alias
        # Padrão: FROM Tabela [alias] ou FROM Tabela alias
        from_pattern = r'FROM\s+([\w\s,]+?)(?:\s+WHERE|\s+JOIN|$)'
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
        join_pattern = r'JOIN\s+([\w]+)(?:\s+(\w+))?\s+ON'
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
        
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, query, re.IGNORECASE)
        
        if select_match:
            select_clause = select_match.group(1)
            if select_clause.strip() != '*':
                for attr in select_clause.split(','):
                    attr = re.sub(r'\s+AS\s+\w+', '', attr, flags=re.IGNORECASE)
                    attr = attr.strip()
                    if '.' in attr:
                        attributes.append(attr)
        
        where_pattern = r'WHERE\s+(.*?)(?:$|\s+ORDER|\s+GROUP)'
        where_match = re.search(where_pattern, query, re.IGNORECASE)
        
        if where_match:
            where_clause = where_match.group(1)
            attr_pattern = r'(\w+\.\w+)'
            attr_matches = re.finditer(attr_pattern, where_clause)
            for match in attr_matches:
                attributes.append(match.group(1))
        
        on_pattern = r'ON\s+([\w.]+)\s*=\s*([\w.]+)'
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
        
        operator_pattern = r'[=<>!]+|AND|OR'
        operators = re.findall(operator_pattern, query, re.IGNORECASE)
        
        for op in operators:
            op_upper = op.upper()
            if op_upper not in self.valid_operators and op_upper not in ['AND', 'OR']:
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