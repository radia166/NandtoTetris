class SymbolTable:
    STATIC = 'STATIC'
    FIELD = 'FIELD'
    ARG = 'ARG'
    VAR = 'VAR'
    CLASS = 'CLASS'
    NONE = 'NONE'

    def __init__(self):
        self.current_class = None
        self.class_table = {}
        self.subroutine_table = {}
        self.index_counters = {
            SymbolTable.STATIC: 0,
            SymbolTable.FIELD: 0,
            SymbolTable.ARG: 0,
            SymbolTable.VAR: 0
        }

    def start_subroutine(self):
        self.subroutine_table = {}
        self.index_counters[SymbolTable.ARG] = 0
        self.index_counters[SymbolTable.VAR] = 0

    def define(self, name, var_type, kind):
        kind = kind.upper()
        index = self.index_counters[kind]
        self.index_counters[kind] += 1

        symbol = {
            'type': var_type,
            'kind': kind,
            'index': index
        }

        if kind in (SymbolTable.STATIC, SymbolTable.FIELD):
            self.class_table[name] = symbol
        elif kind in (SymbolTable.ARG, SymbolTable.VAR):
            self.subroutine_table[name] = symbol
        else:
            pass
        print(f"Defining variable - Name: {name}, Type: {var_type}, Kind: {kind}, Index: {index}")

    def var_count(self, kind):
        return self.index_counters.get(kind, 0)

    def kind_of(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table[name]['kind'].upper()
        elif name in self.class_table:
            return self.class_table[name]['kind'].upper()
        elif name in ["Math", "Memory", "Keyboard", "Screen", "Output", "String", "Array", self.current_class]:
            return SymbolTable.CLASS
        else:
            print(f"DEBUG: No kind found for '{name}', returning NONE.")
            return SymbolTable.NONE

    def type_of(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table[name]['type']
        elif name in self.class_table:
            return self.class_table[name]['type']
        elif name in ["Math", "Memory", "Keyboard", "Screen", "Output", "String", "Array"]:
            return name
        elif name == self.current_class:
            return name
        else:
            print(f"DEBUG: No type found for '{name}', returning None.")
            return None

    def index_of(self, name):
        if name in self.subroutine_table:
            return self.subroutine_table[name]['index']
        elif name in self.class_table:
            return self.class_table[name]['index']
        else:
            return None