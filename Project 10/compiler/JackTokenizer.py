import re

class JackTokenizer:
    KEYWORD = {
        'class', 'constructor', 'function', 'method', 'field', 'static', 'var',
        'int', 'char', 'boolean', 'void', 'true', 'false', 'null', 'this',
        'let', 'do', 'if', 'else', 'while', 'return'
    }

    SYMBOL = {
    '{', '}', '(', ')', '[', ']', '.', ',', ';',
    '+', '-', '*', '/', '&', '|', '<', '>', '=', '~'
    }

    # Regular expressions for token types
    INT_CONST = r'\d+'
    STRING_CONST = r'"[^"\n]*"'
    IDENTIFIER = r'[a-zA-Z_]\w*'

    def __init__(self, input_file):
        with open(input_file, 'r') as file:
            self.input = file.read()

        # Remove comments
        self.input = re.sub(r'//.*|/\*(.|\n)*?\*/', '', self.input)

        # Token list
        self.tokens = self.tokenize()
        self.current_index = -1  # start before the first token
        self.current_token_type = None
        self.current_token_value = None

    def tokenize(self):
        token_specification = [
            ('KEYWORD', r'\b(?:' + '|'.join(self.KEYWORD) + r')\b'),
            ('SYMBOL', r'[{}()[\].,;+\-*/&|<>=~]'),
            ('INT_CONST', r'\d+'),
            ('STRING_CONST', r'"[^"\n]*"'),
            ('IDENTIFIER', r'[a-zA-Z_]\w*'),
            ('SKIP', r'[ \t\n]+'),
            ('MISMATCH', r'.')
        ]
        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
        get_token = re.compile(tok_regex).match
        line = self.input
        pos = 0
        tokens = []
        while pos < len(line):
            mo = get_token(line, pos)
            if mo is None:
                break
            kind = mo.lastgroup
            value = mo.group()
            if kind == 'KEYWORD':
                tokens.append(('KEYWORD', value))
            elif kind == 'SYMBOL':
                tokens.append(('SYMBOL', value))
            elif kind == 'IDENTIFIER':
                tokens.append(('IDENTIFIER', value))
            elif kind == 'INT_CONST':
                tokens.append(('INT_CONST', value))
            elif kind == 'STRING_CONST':
                tokens.append(('STRING_CONST', value[1:-1]))  # Remove quotes
            elif kind == 'SKIP':
                pass
            elif kind == 'MISMATCH':
                raise RuntimeError(f'Unexpected character {value!r} at position {pos}')
            pos = mo.end()
        self.tokens = tokens
        return tokens

    def has_more_tokens(self):
        return self.current_index + 1 < len(self.tokens)

    def advance(self):
        if self.has_more_tokens():
            self.current_index += 1
            self.current_token_type, self.current_token_value = self.tokens[self.current_index]
        else:
            self.current_token_type, self.current_token_value = None, None


    def token_type(self):
        return self.current_token_type

    def keyword(self):
        if self.token_type() == 'KEYWORD':
            return self.current_token_value

    def peek(self):
        if self.current_index + 1 < len(self.tokens):
            next_tt, next_token_value = self.tokens[self.current_index + 1]
            return next_tt, next_token_value
        return None, None

    def peek_token_value(self):
        if self.current_index + 1 < len(self.tokens):
            next_token = self.tokens[self.current_index + 1]
            return next_token
        return None

    def symbol(self):
        if self.token_type() == 'SYMBOL':
            symbol = self.current_token_value
            return symbol
        return self.current_token_value

    def identifier(self):
        if self.token_type() == 'IDENTIFIER':
            return self.current_token_value

    def int_val(self):
        if self.token_type() == 'INT_CONST':
            return int(self.current_token_value)

    def string_val(self):
        if self.token_type() == 'STRING_CONST':
            return self.current_token_value


