import os
import sys

from JackTokenizer import JackTokenizer
from CompilationEngine import CompilationEngine


class JackAnalyzer:
    def __init__(self, source_dir):
        self.targets = self.get_targets(source_dir)

    def get_targets(self, source_dir):
        targets = []
        if os.path.isfile(source_dir):
            if not source_dir.endswith('.jack'):
                raise ValueError(f'Target {source_dir} is not a valid source file')
            targets.append(source_dir)
        elif os.path.isdir(source_dir):
            files = os.listdir(source_dir)
            jack_files = [os.path.join(source_dir, file) for file in files if file.endswith('.jack')]
            if not jack_files:
                raise ValueError(f'Folder {source_dir} does not contain any Jack files')
            targets.extend(jack_files)
        return targets

    def analyze(self):
        global output_file
        for target in self.targets:
            print(f'Parsing {target}')

            tokenizer = JackTokenizer(target)
            target_dir = os.path.dirname(target)

            tokens_output_file = os.path.join(target_dir, os.path.basename(target).replace('.jack', 'T.xml'))
            with open(tokens_output_file, 'w') as token_file:
                token_file.write("<tokens>\n")
                while tokenizer.has_more_tokens():
                    tokenizer.advance()
                    tt = tokenizer.token_type()
                    if tt == 'KEYWORD':
                        token_file.write(f"<keyword> {tokenizer.keyword()} </keyword>\n")
                    elif tt == 'SYMBOL':
                        symbol = tokenizer.symbol()
                        if symbol == '<':
                            symbol = '&lt;'
                        elif symbol == '>':
                            symbol = '&gt;'
                        elif symbol == '&':
                            symbol = '&amp;'
                        token_file.write(f"<symbol> {symbol} </symbol>\n")
                    elif tt == 'IDENTIFIER':
                        token_file.write(f"<identifier> {tokenizer.identifier()} </identifier>\n")
                    elif tt == 'INT_CONST':
                        token_file.write(f"<integerConstant> {tokenizer.int_val()} </integerConstant>\n")
                    elif tt == 'STRING_CONST':
                        token_file.write(f"<stringConstant> {tokenizer.string_val()} </stringConstant>\n")
                token_file.write("</tokens>\n")

            tokenizer = JackTokenizer(target)

            output_file = os.path.join(target_dir, os.path.basename(target).replace('.jack', '.xml'))
            if os.path.exists(output_file):
                os.remove(output_file)
            compiler = CompilationEngine(tokenizer, output_file)
            compiler.compile_class()

            print(f'{target} parsed successfully')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} [source]')
        exit()
    analyzer = JackAnalyzer(sys.argv[1])
    analyzer.analyze()
