class CompilationEngine:
    def __init__(self, tokenizer, output_file):
        self.tokenizer = tokenizer
        self.output_file = output_file
        self.xml_output = []
        self.indent_level = 0
        self.compile_class()
        self.save_output()

    # compiling a class
    def compile_class(self):
        self.write("<class>")
        self.indent_level += 1
        self.advance()

        self.write(self.token()) #class keyword
        self.advance()
        self.write(self.token()) # class name
        self.advance()
        self.write(self.token())
        self.advance()

        while self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() in ('static', 'field'):
            self.compile_class_var_dec()

        while self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() in (
                'constructor', 'function', 'method'):
            self.compile_subroutine()

        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '}':
            self.write(self.token())
            self.advance()

        self.indent_level -= 1
        self.write("</class>")
        print("Exiting compile_class")  # Debug

    def compile_class_var_dec(self):
        self.write("<classVarDec>")
        self.indent_level += 1
        while True:
            self.write(self.token())
            self.advance()
            if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ';':
                self.write(self.token())
                self.advance()
                break
        self.indent_level -= 1
        self.write("</classVarDec>")

    def compile_subroutine(self):
        self.write("<subroutineDec>")
        self.indent_level += 1

        self.write(self.token()) # subroutine keyword

        self.advance()

        self.write(self.token()) #  return type
        self.advance()

        print(
            f"Current token (expecting subroutine name): {self.tokenizer.token_type()}, {self.tokenizer.identifier()}")
        self.write(self.token())
        self.advance()

        # opening '(' of
        print(f"Current token (expecting '('): {self.tokenizer.token_type()}, {self.tokenizer.symbol()}")
        self.write(self.token())
        self.advance()

        self.compile_parameter_list()
        self.write(self.token())
        self.advance()
        self.compile_subroutine_body()
        self.indent_level -= 1
        self.write("</subroutineDec>")

    def compile_parameter_list(self):
        self.write("<parameterList>")
        self.indent_level += 1
        while not (self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ')'):
            self.write(self.token())
            self.advance()
        self.indent_level -= 1
        self.write("</parameterList>")

    def compile_subroutine_body(self):
        print("Entering compile_subroutine_body")  # Debug
        self.write("<subroutineBody>")
        self.indent_level += 1
        self.write(self.token())
        self.advance()

        while self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() == 'var':
            self.compile_var_dec()

        self.compile_statements()
        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '}':
            self.write(self.token())
            self.advance()

        self.indent_level -= 1
        self.write("</subroutineBody>")

    def compile_var_dec(self):
        self.write("<varDec>")
        self.indent_level += 1
        while True:
            self.write(self.token())
            self.advance()
            if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ';':
                self.write(self.token())
                self.advance()
                break
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

        self.write(self.token()) # let
        self.advance()

        self.write(self.token()) # variable name
        self.advance()

        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '[':
            self.write(self.token())
            self.advance()
            self.compile_expression()
            self.write(self.token()) # closing bracket
            self.advance()

        self.write(self.token()) # =
        self.advance()
        self.compile_expression()

        self.write(self.token())  # ;
        self.advance()
        self.indent_level -= 1
        self.write("</letStatement>")

    def compile_if(self):
        self.write("<ifStatement>")
        self.indent_level += 1

        self.write(self.token()) # if
        self.advance()
        self.write(self.token())
        self.advance()

        self.compile_expression()
        self.write(self.token())
        self.advance()

        self.write(self.token())
        self.advance()

        self.compile_statements()
        self.write(self.token())
        self.advance()

        if self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() == 'else':
            self.write(self.token())
            self.advance()
            self.write(self.token())
            self.advance()
            self.compile_statements()
            self.write(self.token())
            self.advance()
        self.indent_level -= 1
        self.write("</ifStatement>")

    def compile_while(self):
        self.write("<whileStatement>")
        self.indent_level += 1

        self.write(self.token())
        self.advance()

        self.write(self.token())
        self.advance()

        self.compile_expression()
        self.write(self.token())

        self.advance()
        self.write(self.token())
        self.advance()

        self.compile_statements()
        self.write(self.token())
        self.advance()
        self.indent_level -= 1
        self.write("</whileStatement>")

    def compile_do(self):
        self.write("<doStatement>")
        self.indent_level += 1
        self.write(self.token())
        self.advance()
        self.compile_subroutine_call()
        self.write(self.token())
        self.advance()
        self.indent_level -= 1
        self.write("</doStatement>")

    def compile_return(self):
        self.write("<returnStatement>")
        self.indent_level += 1
        self.write(self.token())
        self.advance()
        if not (self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ';'):
            self.compile_expression()
        self.write(self.token())
        self.advance()
        self.indent_level -= 1
        self.write("</returnStatement>")

    def compile_expression(self):
        self.write("<expression>")
        self.indent_level += 1

        # compile the first term
        self.compile_term()

        operators = ('+', '-', '*', '/', '&', '|', '<', '>', '=')

        while self.tokenizer.token_type() == 'SYMBOL':
            raw_symbol = self.tokenizer.symbol()
            if raw_symbol in operators:

                print(f"Valid operator found: {raw_symbol}")
                self.write_symbol(raw_symbol)
                self.tokenizer.advance()
                self.compile_term()
            else:
                print(f"Not an operator, exiting loop: {raw_symbol}")
                break

        self.indent_level -= 1
        self.write("</expression>")

    def compile_subroutine_call(self):
        self.write(self.token())
        self.advance()

        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '.':
            self.write(self.token()) # .
            self.advance()
            self.write(self.token())
            self.advance()

        self.write(self.token())
        self.advance()
        self.compile_expression_list()
        self.write(self.token())
        self.advance()
        pass

    def compile_term(self):
        self.write("<term>")
        self.indent_level += 1

        tt = self.tokenizer.token_type()

        if tt in ('INT_CONST', 'STRING_CONST', 'KEYWORD'):
            self.write(self.token()) # constant/keyword
            self.tokenizer.advance()

        elif tt == 'IDENTIFIER':
            identifier = self.token()
            self.write(identifier)

            next_tt, next_token = self.tokenizer.peek()
            if next_tt == 'SYMBOL' and next_token in ['[', '(', '.']:
                self.tokenizer.advance()
                symbol = self.tokenizer.symbol()

                if symbol == '[':
                    self.write(self.token())
                    self.tokenizer.advance()
                    self.compile_expression()
                    self.write(self.token())
                    self.tokenizer.advance()

                elif symbol == '(':
                    self.write(self.token())
                    self.tokenizer.advance()
                    self.compile_expression_list()
                    self.write(self.token())
                    self.tokenizer.advance()

                elif symbol == '.':
                    self.write(self.token())
                    self.tokenizer.advance()

                    self.write(self.token()) #subroutine name
                    self.tokenizer.advance()

                    self.write(self.token())
                    self.tokenizer.advance()

                    self.compile_expression_list()
                    self.write(self.token())
                    self.tokenizer.advance()

            else:
                self.tokenizer.advance()

        elif tt == 'SYMBOL' and self.tokenizer.symbol() == '(':
            self.write(self.token())
            self.tokenizer.advance()
            self.compile_expression()
            self.write(self.token())
            self.tokenizer.advance()
        elif tt == 'SYMBOL' and self.tokenizer.symbol() in ('-', '~'):
            self.write(self.token()) # unary operator
            self.tokenizer.advance()
            self.compile_term()

        else:
            pass

        self.indent_level -= 1
        self.write("</term>")

    def compile_expression_list(self):
        self.write("<expressionList>")
        self.indent_level += 1

        if not (self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ')'):
            self.compile_expression()

            while self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == ',':
                self.write(self.token())
                self.advance()
                self.compile_expression()

        self.indent_level -= 1
        self.write("</expressionList>")

    def advance(self):
        self.tokenizer.advance()

   # get and returns the current token in XML format
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
            return f"<identifier> {self.tokenizer.identifier()} </identifier>"
        elif tt == 'INT_CONST':
            return f"<integerConstant> {self.tokenizer.int_val()} </integerConstant>"
        elif tt == 'STRING_CONST':
            return f"<stringConstant> {self.tokenizer.string_val()} </stringConstant>"

        while self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() in ('static', 'field'):
            self.compile_class_var_dec()

        while self.tokenizer.token_type() == 'KEYWORD' and self.tokenizer.keyword() in (
        'constructor', 'function', 'method'):
            self.compile_subroutine()

        if self.tokenizer.token_type() == 'SYMBOL' and self.tokenizer.symbol() == '}':
            self.write(self.token())
            self.advance()

    #XML safe version of symbol
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

    def write(self, content,symbol=''):
        indent = '  ' * self.indent_level
        self.xml_output.append(f"{indent} {content}")
        print(f"Appending to XML output: {indent} {content}") # Debugging

    def save_output(self):
        try:
            print("Saving output...")
            with open(self.output_file, 'w') as file:
                file.write("\n".join(self.xml_output))
            with open(self.output_file, 'w', encoding='utf-8') as file:
                file.write("\n".join(self.xml_output))
        except IOError as e:
            print(f"Error saving output to {self.output_file}: {e}")




