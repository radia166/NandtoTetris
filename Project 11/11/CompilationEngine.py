from SymbolTabble import SymbolTable
from CodeWriter import CodeWriter

class CompilationEngine:
    def __init__(self, tokenizer, xml_output_file, vm_output_file):
        self.class_name = ""
        self.label_count = 0
        self.tokenizer = tokenizer
        self.xml_output_file = xml_output_file
        self.xml_output = []
        self.indent_level = 0
        self.current_class = None
        self.current_function_name = None
        self.symbol_table = SymbolTable()
        self.code_writer = CodeWriter(vm_output_file)

    def new_label(self):
        label = f"{self.class_name}_{self.label_count}"
        self.label_count += 1
        return label
        
    def compile_class(self):
        self.write("<class>")
        self.indent_level += 1
        self.advance()

        # 'class'
        self.write(self.token())
        self.advance()
        self.class_name = self.tokenizer.identifier()

        if self.tokenizer.token_type() == 'IDENTIFIER':
            class_name = self.tokenizer.identifier()
            self.write_identifier(class_name, kind='class', usage='declaration')
            self.advance()
            self.current_class = class_name
        else:
            print(f"Expected class name, but got: {self.tokenizer.token_type()}, {self.tokenizer.current_token_value}")

        #'{'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '{':
            self.write(self.token())
            self.advance()
        else:
            print(f"Expected '{{', but got: {self.tokenizer.token_type()}, {self.tokenizer.current_token_value}")

        while self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() in ('static', 'field'):
            self.compile_class_var_dec()

        while self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() in (
        'constructor', 'function', 'method'):
            self.compile_subroutine()

        #'}'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '}':
            self.write(self.token())
            self.advance()
        else:
            print(f"Expected }} , but got: {self.tokenizer.token_type()}, {self.tokenizer.current_token_value}")
            self.write(self.token())
            self.advance()

        self.indent_level -= 1
        self.write("</class>")
        print("Exiting compile_class")  #debug

    def compile_subroutine(self):
        self.symbol_table.start_subroutine()  #Reset symbol table
        self.write("<subroutineDec>")
        self.indent_level = 0
        print(f"Entering compile_subroutine with token: {self.tokenizer.current_token_value}")

        self.write(self.token())
        subroutine_type = self.tokenizer.current_token_value
        self.advance()

        if self.tokenizer.token_type() in ('KEYWORD', 'IDENTIFIER'):
            return_type = self.tokenizer.current_token_value
            self.write(self.token())
            self.advance()
        else:
            print(f"Unexpected token type for return type: {self.tokenizer.token_type()}")

        if self.tokenizer.token_type() == 'IDENTIFIER':
            subroutine_name = self.tokenizer.identifier()
            self.write_identifier(subroutine_name, kind='subroutine', usage='declaration')
            self.current_function_name = subroutine_name  # Store current function name
            self.advance()
        else:
            print(
                f"Expected subroutine name, but got: {self.tokenizer.token_type()}, {self.tokenizer.current_token_value}")

        # 'this' argument
        if subroutine_type == 'method':
            self.symbol_table.define('this', self.current_class, SymbolTable.ARG)

        #  '('
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '(':
            self.write(self.token())
            self.advance()
        else:
            print(f"Expected '(', but got: {self.tokenizer.token_type()}, {self.tokenizer.current_token_value}")

        self.compile_parameter_list()

        #  ')'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ')':
            self.write(self.token())
            self.advance()
        else:
            print(f"Expected ')', but got: {self.tokenizer.token_type()}, {self.tokenizer.current_token_value}")

        self.compile_subroutine_body()

        self.indent_level -= 1
        self.write("</subroutineDec>")

    def compile_parameter_list(self):
        self.write("<parameterList>")
        self.indent_level += 1
        param_type = None

        if not (self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ')'):
            while True:
                # Handle type
                if self.tokenizer.token_type() == 'KEYWORD':
                    param_type = self.tokenizer.keyword()
                    self.write(self.token())
                elif self.tokenizer.token_type() == 'IDENTIFIER':
                    param_type = self.tokenizer.identifier()
                    self.write_identifier(param_type, usage='type')
                else:
                    print(f"Error: Unexpected token type for parameter type: {self.tokenizer.token_type()}")
                self.advance()

                param_name = self.tokenizer.identifier()
                self.write_identifier(param_name, param_type, SymbolTable.ARG, usage='declaration')
                self.symbol_table.define(param_name, param_type, SymbolTable.ARG)
                self.advance()

                if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ',':
                    self.write(self.token())
                    self.advance()
                else:
                    break

        self.indent_level -= 1
        self.write("</parameterList>")

    def compile_subroutine_body(self):
        self.write("<subroutineBody>")
        self.indent_level += 1
        self.write(self.token())  # '{'
        self.advance()

        while self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() == 'var':
            self.compile_var_dec()

        num_locals = self.symbol_table.var_count(SymbolTable.VAR)
        function_name = f"{self.current_class}.{self.current_function_name}"
        self.code_writer.write_function(function_name, num_locals)

        if self.current_function_name == 'new':
            field_count = self.symbol_table.var_count(SymbolTable.FIELD)
            self.code_writer.write_push('constant', field_count)
            self.code_writer.write_call('Memory.alloc', 1)
            self.code_writer.write_pop('pointer', 0)  # Set 'this'

        elif self.symbol_table.kind_of('this') == SymbolTable.ARG:
            self.code_writer.write_push('argument', 0)
            self.code_writer.write_pop('pointer', 0)

        self.compile_statements()

        # '}'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '}':
            self.write(self.token())
            self.advance()

        self.indent_level -= 1
        self.write("</subroutineBody>")

    def compile_class_var_dec(self):
        self.write("<classVarDec>")
        self.indent_level += 1
        print(f"Entering compile_class_var_dec with token: {self.tokenizer.current_token_value}")

        # 'static' or 'field'
        kind = self.tokenizer.keyword()
        self.write(self.token())
        self.advance()

        # variable type
        if self.tokenizer.token_type() == 'KEYWORD':
            var_type = self.tokenizer.keyword()
            self.write(self.token())
            self.advance()
        elif self.tokenizer.token_type() == 'IDENTIFIER':
            var_type = self.tokenizer.identifier()
            self.write_identifier(var_type, usage='type')
            self.advance()
        else:
            # error handling
            var_type = None
            print(f"Error: Unexpected token type for variable type: {self.tokenizer.token_type()}")
            self.advance()

        var_name = self.tokenizer.identifier()
        self.write_identifier(var_name, var_type, kind, usage='declaration')
        self.symbol_table.define(var_name, var_type, kind)
        self.advance()

        while self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ',':
            self.write(self.token())
            self.advance()

            var_name = self.tokenizer.identifier()
            self.write_identifier(var_name, var_type, kind, usage='declaration')
            self.symbol_table.define(var_name, var_type, kind)
            self.advance()

        # ';'
        self.write(self.token())
        self.advance()

        self.indent_level -= 1
        self.write("</classVarDec>")
        print(f"Exiting compile_class_var_dec with token: {self.tokenizer.current_token_value}")

    def compile_var_dec(self):
        self.write("<varDec>")
        self.indent_level += 1

        # 'var'
        kind = SymbolTable.VAR
        self.write(self.token())
        self.advance()

        var_type = self.tokenizer.current_token_value
        self.write(self.token())
        self.advance()

        while True:
            var_name = self.tokenizer.identifier()
            self.write_identifier(var_name, var_type, kind, usage='declaration')
            self.symbol_table.define(var_name, var_type, kind)
            self.advance()

            if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ',':
                self.write(self.token())  # ','
                self.advance()
            else:
                break

        self.write(self.token())  # ';'
        self.advance()
        self.indent_level -= 1
        self.write("</varDec>")

    def compile_statements(self):
        self.write("<statements>")
        self.indent_level += 1

        while self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() in (
                'let', 'if', 'while', 'do', 'return'):
            current_keyword = self.tokenizer.keyword()

            if current_keyword == 'let':
                self.compile_let()
            elif current_keyword == 'if':
                self.compile_if()
            elif current_keyword == 'while':
                self.compile_while()
            elif current_keyword == 'do':
                self.compile_do()
            elif current_keyword == 'return':
                self.compile_return()

        self.indent_level -= 1
        self.write("</statements>")

    def compile_let(self):
        self.write("<letStatement>")
        self.indent_level += 1

        #'let'
        self.write(self.token())
        self.advance()

        if self.tokenizer.token_type() == 'IDENTIFIER':
            var_name = self.tokenizer.identifier()
            self.write_identifier(var_name, usage='used')
            self.advance()
        else:
            raise ValueError(f"Expected variable name after 'let', but got: {self.tokenizer.token_type()}")

        # Debug
        kind = self.symbol_table.kind_of(var_name)
        if kind == SymbolTable.NONE:
            raise ValueError(f"Undefined variable '{var_name}' found while trying to generate VM code")

        var_type = self.symbol_table.type_of(var_name)
        index = self.symbol_table.index_of(var_name)
        segment = self.get_segment(kind)
        print(f"Handling let statement for variable: {var_name}, kind: {kind}, type: {var_type}, index: {index}")

        if segment:
            pass
        else:
            print(f"ERROR: Invalid segment for kind '{kind}'. Variable '{var_name}' may not be declared.")

        is_array = False
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '[':
            is_array = True
            #  '['
            self.write(self.token())
            self.advance()

            self.compile_expression()

            # ']'
            self.write(self.token())
            self.advance()

            self.code_writer.write_push(self.get_segment(kind), index)
            self.code_writer.write_arithmetic('add')

        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '=':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected '=' in let statement, but got: {self.tokenizer.token_type()}")

        self.compile_expression()

        if is_array:
            # pop the value into 'that'
            self.code_writer.write_pop('temp', 0)
            self.code_writer.write_pop('pointer', 1)
            self.code_writer.write_push('temp', 0)
            self.code_writer.write_pop('that', 0)
        else:
            self.code_writer.write_pop(self.get_segment(kind), index)

        #  ';'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ';':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected ';' at the end of let statement, but got: {self.tokenizer.token_type()}")

        self.indent_level -= 1
        self.write("</letStatement>")

    def compile_if(self):
        self.write("<ifStatement>")
        self.indent_level += 1

        # 'if'
        self.write(self.token())
        self.advance()

        # '('
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '(':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected '(', but got: {self.tokenizer.current_token_value}")

        self.compile_expression()

        # ')'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ')':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected ')', but got: {self.tokenizer.current_token_value}")

        label_true = self.new_label()
        label_end = self.new_label()


        self.code_writer.write_arithmetic("not")
        self.code_writer.write_if(label_true)

        # '{'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '{':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected '{{', but got: {self.tokenizer.current_token_value}")

        self.compile_statements()

        # '}'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '}':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected '}}', but got: {self.tokenizer.current_token_value}")

        self.code_writer.write_goto(label_end)
        self.code_writer.write_label(label_true)

        # check 'else' clause
        if self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() == 'else':
            # 'else'
            self.write(self.token())
            self.advance()

            # '{'
            if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '{':
                self.write(self.token())
                self.advance()
            else:
                raise ValueError(f"Expected '{{' after 'else', but got: {self.tokenizer.current_token_value}")

            self.compile_statements()

            # '}'
            if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '}':
                self.write(self.token())
                self.advance()
            else:
                raise ValueError(f"Expected '}}', but got: {self.tokenizer.current_token_value}")

        self.code_writer.write_label(label_end)

        self.indent_level -= 1
        self.write("</ifStatement>")

    def compile_while(self):
        self.write("<whileStatement>")
        self.indent_level += 1

        # 'while'
        self.write(self.token())
        self.advance()

        # '('
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '(':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected '(', but got: {self.tokenizer.current_token_value}")

        loop_label = self.new_label()
        end_label = self.new_label()

        self.code_writer.write_label(loop_label)

        self.compile_expression()

        # ')'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ')':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected ')', but got: {self.tokenizer.current_token_value}")

        self.code_writer.write_arithmetic('not')
        self.code_writer.write_if(end_label)

        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '{':
            self.write(self.token())  # '{'
            self.advance()
        else:
            raise ValueError(f"Expected '{{', but got: {self.tokenizer.current_token_value}")

        self.compile_statements()

        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '}':
            self.write(self.token())  # '}'
            self.advance()
        else:
            raise ValueError(f"Expected '}}', but got: {self.tokenizer.current_token_value}")

        self.code_writer.write_goto(loop_label)
        self.code_writer.write_label(end_label)

        self.indent_level -= 1
        self.write("</whileStatement>")


    def compile_do(self):
        self.write("<doStatement>")
        self.indent_level += 1

        # 'do'
        self.write(self.token())
        self.advance()

        self.compile_subroutine_call()

        self.code_writer.write_pop('temp', 0)

        # ';'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ';':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected ';' after 'do' statement, but got: {self.tokenizer.current_token_value}")

        self.indent_level -= 1
        self.write("</doStatement>")

    def compile_return(self):
        self.write("<returnStatement>")
        self.indent_level += 1

        # 'return'
        self.write(self.token())
        self.advance()

        if not (self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ';'):
            self.compile_expression()
        else:
            self.code_writer.write_push('constant', 0)

        # ';'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ';':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected ';' at the end of return statement, but got: {self.tokenizer.token_type()}")

        self.code_writer.write_return()

        self.indent_level -= 1
        self.write("</returnStatement>")

    def compile_expression(self):
        self.compile_term()
        operators = {
            '+': 'add',
            '-': 'sub',
            '*': 'Math.multiply',
            '/': 'Math.divide',
            '&': 'and',
            '|': 'or',
            '<': 'lt',
            '>': 'gt',
            '=': 'eq'
        }

        while self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() in operators:
            operator = self.tokenizer.symbol()
            self.write_symbol(operator)  # Write the operator to XML
            self.advance()
            self.compile_term()

            if operator in ('*', '/'):
                self.code_writer.write_call(operators[operator].split()[0], 2)
            else:
                self.code_writer.write_arithmetic(operators[operator])

    def compile_subroutine_call(self):
        name = self.tokenizer.identifier()
        self.advance()

        n_args = 0

        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '.':
            self.advance()

            subroutine_name = self.tokenizer.identifier()
            self.advance()

            kind = self.symbol_table.kind_of(name)
            print(f"DEBUG: Kind lookup for '{name}': {kind}")

            if kind == SymbolTable.CLASS:
                full_name = f"{name}.{subroutine_name}"
                print(f"DEBUG: Treating '{full_name}' as a class function.")
            elif kind != SymbolTable.NONE:
                var_type = self.symbol_table.type_of(name)
                index = self.symbol_table.index_of(name)
                segment = self.get_segment(kind)
                self.code_writer.write_push(segment, index)
                n_args += 1
                full_name = f"{var_type}.{subroutine_name}"
                print(f"DEBUG: Calling method of instance '{name}' of type '{var_type}', with index '{index}'")
            else:
                full_name = f"{name}.{subroutine_name}"
                print(f"DEBUG: Treating '{full_name}' as a class function.")
        else:
            subroutine_name = name
            full_name = f"{self.current_class}.{subroutine_name}"
            self.code_writer.write_push('pointer', 0)  # Push 'this'
            n_args += 1  # Increment n_args for 'this'
            print(f"DEBUG: Treating '{full_name}' as a method of this class.")

        # '('
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '(':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected '(' after subroutine call, but got: {self.tokenizer.current_token_value}")

        n_args += self.compile_expression_list()

        #  ')'
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ')':
            self.write(self.token())
            self.advance()
        else:
            raise ValueError(f"Expected ')' after expression list, but got: {self.tokenizer.current_token_value}")

        print(f"DEBUG: Writing VM call for '{full_name}' with {n_args} arguments.")
        self.code_writer.write_call(full_name, n_args)

    def compile_term(self):
        self.write("<term>")
        self.indent_level += 1

        tt = self.tokenizer.token_type()
        current_token = self.tokenizer.current_token_value

        print(f"Compiling term. Current token type: '{tt}', Current token: '{current_token}'")

        if tt == 'INT_CONST':
            # integer constant
            value = self.tokenizer.int_val()
            self.write(f"<integerConstant> {value} </integerConstant>")
            self.code_writer.write_push("constant", value)
            self.advance()

        elif tt == 'STRING_CONST':
            # string constant
            value = self.tokenizer.string_val()
            escaped_value = self.escape_xml(value)
            self.write(f'<stringConstant> {escaped_value} </stringConstant>')
            self.code_writer.write_push_string(value)
            self.advance()

        elif tt == 'KEYWORD':
            # 'true', 'false', 'null', 'this'
            keyword = self.tokenizer.keyword()
            self.write(self.token())
            self.handle_keyword_constant(keyword)
            self.advance()

        elif tt == 'IDENTIFIER':
            var_name = self.tokenizer.identifier()
            next_tt, next_token = self.tokenizer.peek()

            if next_tt == 'SYMBOL' and next_token == '[':
                # Array access
                self.write_identifier(var_name, usage='used')
                self.advance()

                self.write(self.token())  # '['
                self.advance()

                self.compile_expression()

                if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ']':
                    self.write(self.token())  # ']'
                    self.advance()
                else:
                    raise ValueError(f"Expected ']', but got: {self.tokenizer.current_token_value}")

                kind = self.symbol_table.kind_of(var_name)
                index = self.symbol_table.index_of(var_name)
                segment = self.get_segment(kind)
                if segment:
                    self.code_writer.write_push(segment, index)
                    print(f"DEBUG: Writing VM command: push {segment} {index}")
                else:
                    print(f"ERROR: Invalid segment for kind '{kind}'. Variable '{var_name}' may not be declared.")

                self.code_writer.write_arithmetic('add')
                self.code_writer.write_pop('pointer', 1)
                self.code_writer.write_push('that', 0)

            elif next_tt == 'SYMBOL' and next_token in ['(', '.']:
                self.compile_subroutine_call()

            else:
                self.write_identifier(var_name, usage='used')
                self.advance()

                kind = self.symbol_table.kind_of(var_name)
                index = self.symbol_table.index_of(var_name)
                segment = self.get_segment(kind)
                if segment:
                    self.code_writer.write_push(segment, index)
                    print(f"DEBUG: Writing VM command: push {segment} {index}")
                else:
                    print(f"ERROR: Invalid segment for kind '{kind}'. Variable '{var_name}' may not be declared.")

        elif tt == 'SYMBOL' and self.tokenizer.symbol() == '(':
            self.write(self.token())  # '('
            self.advance()
            self.compile_expression()
            if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ')':
                self.write(self.token())  # ')'
                self.advance()
            else:
                raise ValueError(f"Expected ')', but got: {self.tokenizer.current_token_value}")

        elif tt == 'SYMBOL' and self.tokenizer.symbol() in ('-', '~'):
            # Unary operator
            op = self.tokenizer.symbol()
            self.write(self.token())
            self.advance()
            self.compile_term()
            if op == '-':
                self.code_writer.write_arithmetic('neg')
            elif op == '~':
                self.code_writer.write_arithmetic('not')
        else:
            raise ValueError(f"Unexpected token type '{tt}' in compile_term")

        self.indent_level -= 1
        self.write("</term>")

    def compile_expression_list(self):
        self.write("<expressionList>")
        self.indent_level += 1

        n_args = 0

        if not (self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ')'):
            self.compile_expression()
            n_args += 1

            while self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ',':
                self.write(self.token())
                self.advance()
                self.compile_expression()
                n_args += 1

        self.indent_level -= 1
        self.write("</expressionList>")
        return n_args

    def advance(self):
        self.tokenizer.advance()

    def token(self):
        tt = self.tokenizer.token_type()
        if tt == 'KEYWORD':
            return f"<keyword> {self.tokenizer.keyword()} </keyword>"
        elif tt == 'SYMBOL':
            symbol = self.tokenizer.symbol()
            if symbol == '<':
                symbol = '&lt;'
            elif symbol == '>':
                symbol = '&gt;'
            elif symbol == '&':
                symbol = '&amp;'
            return f"<symbol> {symbol} </symbol>"
        elif tt == 'IDENTIFIER':
            identifier = self.tokenizer.identifier()
            return f"<identifier> {identifier} </identifier>"

        elif tt == 'INT_CONST':
            return f"<integerConstant> {self.tokenizer.int_val()} </integerConstant>"
        elif tt == 'STRING_CONST':
            return f"<stringConstant> {self.tokenizer.string_val()} </stringConstant>"
        else:
            return None

    def write_symbol(self, symbol):
        if symbol == '<':
            escaped_symbol = '&lt;'
        elif symbol == '>':
            escaped_symbol = '&gt;'
        elif symbol == '&':
            escaped_symbol = '&amp;'
        else:
            escaped_symbol = symbol
        self.write(f"<symbol> {escaped_symbol} </symbol>")

    def write(self, content):
        indent = '  ' * self.indent_level
        self.xml_output.append(indent + content)
        print(f"Appending to XML output: {indent} {content}") # Debugging

    def save_output(self):
        try:
            print("Saving output...")
            with open(self.xml_output_file, 'w') as file:
                file.write("\n".join(self.xml_output))
            with open(self.xml_output_file, 'w', encoding='utf-8') as file:
                file.write("\n".join(self.xml_output))
        except IOError as e:
            print(f"Error saving output to {self.xml_output_file}: {e}")

    def escape_xml(self, text):
        return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;"))

    def write_identifier(self, name, var_type=None, kind=None, usage=None, index=None):
        attributes = []
        if kind:
            attributes.append(f'kind="{kind}"')
        if var_type:
            attributes.append(f'type="{var_type}"')
        if usage:
            attributes.append(f'usage="{usage}"')
        if index is not None:
            attributes.append(f'index="{index}"')
        attr_str = ' '.join(attributes)
        self.write(f'<identifier {attr_str}> {name} </identifier>')

    def write_operator(self, operator):
        if operator == '+':
            self.code_writer.write_arithmetic('add')
        elif operator == '-':
            self.code_writer.write_arithmetic('sub')
        elif operator == '*':
            self.code_writer.write_call('Math.multiply', 2)
        elif operator == '/':
            self.code_writer.write_call('Math.divide', 2)
        elif operator == '&':
            self.code_writer.write_arithmetic('and')
        elif operator == '|':
            self.code_writer.write_arithmetic('or')
        elif operator == '<':
            self.code_writer.write_arithmetic('lt')
        elif operator == '>':
            self.code_writer.write_arithmetic('gt')
        elif operator == '=':
            self.code_writer.write_arithmetic('eq')
        else:
            raise ValueError(f"Unknown operator: {operator}")

    def compile_string(self, value):
        length = len(value)
        self.code_writer.write_vm_command(f"push constant {length}")
        self.code_writer.write_vm_command("call String.new 1")

        for char in value:
            char_code = ord(char)
            self.code_writer.write_vm_command(f"push constant {char_code}")
            self.code_writer.write_vm_command("call String.appendChar 2")

    def handle_keyword_constant(self, keyword):
        # 'true', 'false', 'null', and 'this'
        if keyword == 'true':
            self.code_writer.write_push('constant', 1)
            self.code_writer.write_arithmetic('neg')
        elif keyword == 'false' or keyword == 'null':
            # null, false = 0
            self.code_writer.write_push('constant', 0)
        elif keyword == 'this':
            # 'this'
            self.code_writer.write_push('pointer', 0)
        else:
            raise ValueError(f"Unknown keyword constant: {keyword}")

    def get_segment(self, kind):
        segment_map = {
            'STATIC': 'static',
            'FIELD': 'this',
            'ARG': 'argument',
            'VAR': 'local',
            'NONE': None,
            'CLASS': None
        }
        kind_upper = kind.upper()
        segment = segment_map.get(kind_upper)
        print(f"DEBUG: get_segment called with kind='{kind_upper}', returning segment='{segment}'")
        if segment is None and kind_upper not in ['NONE', 'CLASS']:
            print(f"ERROR: Invalid segment for kind '{kind_upper}'")
        return segment

    def close_vm_output(self):
        self.code_writer.close()
