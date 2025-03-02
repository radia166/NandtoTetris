#Radia Tabassum , id:2402355
import sys


class CodeWriter:
    def __init__(self, output_file):
            self.label_counter = 0
            self.ofd = open(output_file, 'w')
            self.file_name = None

    def set_file_name(self, file_name):
            self.file_name = file_name.split("/")[-1].replace(".vm", "")

    def close(self):
        print(f"Closing file: {self.ofd.name}")
        self.ofd.close()

    def op_push(self, memorysegment, index):
        segment_map = {
                "local": "LCL",
                "argument": "ARG",
                "this": "THIS",
                "that": "THAT",
                "temp": "R5" # temp starts at R5
        }

        if memorysegment == "constant":
            self.ofd.write(f"// push constant {index}\n")
            self.ofd.write(f"@{index}\n")
            self.ofd.write("D=A\n") # D=constant value
            self.ofd.write("@SP\n")
            self.ofd.write("A=M\n")
            self.ofd.write("M=D\n") # Push value onto stack
            self.ofd.write("@SP\n")
            self.ofd.write("M=M+1\n")

        elif memorysegment in segment_map:
            self.ofd.write(f"// push {memorysegment} {index}\n")
            self.ofd.write(f"@{index}\n")
            self.ofd.write("D=A\n")
            self.ofd.write(f"@{segment_map[memorysegment]}\n")
            self.ofd.write("A=D+M\n" if memorysegment != "temp" else "A=D+A\n")  # get address
            self.ofd.write("D=M\n")
            self.ofd.write("@SP\n")
            self.ofd.write("A=M\n")
            self.ofd.write("M=D\n") # Push value onto stack
            self.ofd.write("@SP\n")
            self.ofd.write("M=M+1\n")

        elif memorysegment == "static":
            self.ofd.write(f"// push static {index}\n")
            self.ofd.write(f"@{self.file_name}.{index}\n")
            self.ofd.write("D=M\n")
            self.ofd.write("@SP\n")
            self.ofd.write("A=M\n")
            self.ofd.write("M=D\n")
            self.ofd.write("@SP\n")
            self.ofd.write("M=M+1\n")

        elif memorysegment == "pointer":
            self.ofd.write(f"// push pointer {index}\n")
            if index == "0":
                self.ofd.write("@THIS\n")
            elif index == "1":
                self.ofd.write("@THAT\n")
            self.ofd.write("D=M\n")
            self.ofd.write("@SP\n")
            self.ofd.write("A=M\n")
            self.ofd.write("M=D\n")
            self.ofd.write("@SP\n")
            self.ofd.write("M=M+1\n")

        else:
            raise Exception(f"Unknown memory segment: {memorysegment}")

    def op_pop(self, memorysegment, index):
        segment_map = {
            "local": "LCL",
            "argument": "ARG",
            "this": "THIS",
            "that": "THAT",
            "temp": "R5"
        }

        if memorysegment in segment_map:
            self.ofd.write(f"// pop {memorysegment} {index}\n")
            self.ofd.write(f"@{index}\n")
            self.ofd.write("D=A\n")
            self.ofd.write(f"@{segment_map[memorysegment]}\n")
            self.ofd.write("D=D+M\n" if memorysegment != "temp" else "D=D+A\n")  # Get address
            self.ofd.write("@R13\n") # Use temp register to store address
            self.ofd.write("M=D\n")
            self.ofd.write("@SP\n")
            self.ofd.write("AM=M-1\n")  # pop the top value
            self.ofd.write("D=M\n")
            self.ofd.write("@R13\n")
            self.ofd.write("A=M\n")
            self.ofd.write("M=D\n")

        elif memorysegment == "static":
            self.ofd.write(f"// pop static {index}\n")
            self.ofd.write("@SP\n")
            self.ofd.write("AM=M-1\n") #pop the top value
            self.ofd.write("D=M\n") #popped value in D
            self.ofd.write(f"@{self.file_name}.{index}\n")
            self.ofd.write("M=D\n")

        elif memorysegment == "pointer":
            self.ofd.write(f"// pop pointer {index}\n")
            self.ofd.write("@SP\n")
            self.ofd.write("AM=M-1\n")
            self.ofd.write("D=M\n")
            if index == "0":
                self.ofd.write("@THIS\n")
            elif index == "1":
                self.ofd.write("@THAT\n")
            self.ofd.write("M=D\n")

        else:
            raise Exception(f"Unknown memory segment: {memorysegment}")

    def op_arithmetic(self, command): #dispatcher
        if command == "add":
            self.op_add()
        elif command == "sub":
            self.op_sub()
        elif command == "neg":
            self.op_neg()
        elif command == "eq":
            self.op_eq()
        elif command == "gt":
            self.op_gt()
        elif command == "lt":
            self.op_lt()
        elif command == "and":
            self.op_and()
        elif command == "or":
            self.op_or()
        elif command == "not":
            self.op_not()
        else:
            raise Exception(f"unknown arithmetic command: {command}")

    def op_add(self):
        self.ofd.write("// add\n")
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")
        self.ofd.write("D=M\n")  #Store y in D
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")
        self.ofd.write("M=D+M\n") # x = x + y
        self.ofd.write("@SP\n")
        self.ofd.write("M=M+1\n")


    def op_sub(self):
        self.ofd.write("// sub\n")
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")  #pop y
        self.ofd.write("D=M\n")  # D = y
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")  # pop x
        self.ofd.write("M=M-D\n")  # x = x - y
        self.ofd.write("@SP\n")
        self.ofd.write("M=M+1\n")

    def op_neg(self):
        self.ofd.write("// neg\n")
        self.ofd.write("@SP\n")
        self.ofd.write("A=M-1\n")
        self.ofd.write("M=-M\n")  # Neg top value

    def op_eq(self):
        self.label_counter += 1
        label = f"EQ_{self.label_counter}"
        self.ofd.write(f"// eq\n")
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")  #pop y
        self.ofd.write("D=M\n")  # D = y
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")  #pop x
        self.ofd.write("D=M-D\n")  # D = x - y
        self.ofd.write(f"@{label}_TRUE\n")
        self.ofd.write("D;JEQ\n")  # Jump to EQ_TRUE, if x == y
        self.ofd.write("@SP\n")
        self.ofd.write("A=M\n")
        self.ofd.write("M=0\n")  #False (0)
        self.ofd.write(f"@{label}_END\n")
        self.ofd.write("0;JMP\n")  # Jump to EQ_END
        self.ofd.write(f"({label}_TRUE)\n")
        self.ofd.write("@SP\n")
        self.ofd.write("A=M\n")
        self.ofd.write("M=-1\n")  #True (-1)
        self.ofd.write(f"({label}_END)\n")
        self.ofd.write("@SP\n")
        self.ofd.write("M=M+1\n")

    def op_lt(self):
        self.label_counter += 1
        label = f"LT_{self.label_counter}"
        self.ofd.write(f"// lt\n")
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")  #pop y
        self.ofd.write("D=M\n")
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")  #pop x
        self.ofd.write("D=M-D\n")  # D = x - y
        self.ofd.write(f"@{label}_TRUE\n")
        self.ofd.write("D;JLT\n")  # Jump to LT_TRUE, if x < y
        self.ofd.write("@SP\n")
        self.ofd.write("A=M\n")
        self.ofd.write("M=0\n")  # False (0)
        self.ofd.write(f"@{label}_END\n")
        self.ofd.write("0;JMP\n")
        self.ofd.write(f"({label}_TRUE)\n")
        self.ofd.write("@SP\n")
        self.ofd.write("A=M\n")
        self.ofd.write("M=-1\n")  # True (-1)
        self.ofd.write(f"({label}_END)\n")
        self.ofd.write("@SP\n")
        self.ofd.write("M=M+1\n")

    def op_gt(self):
        self.label_counter += 1
        label = f"GT_{self.label_counter}"
        self.ofd.write(f"// gt\n")
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")
        self.ofd.write("D=M\n")  # D = y
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")
        self.ofd.write("D=M-D\n")  # D = x - y
        self.ofd.write(f"@{label}_TRUE\n")
        self.ofd.write("D;JGT\n")  # Jump to GT_TRUE,if x > y
        self.ofd.write("@SP\n")
        self.ofd.write("A=M\n")
        self.ofd.write("M=0\n")
        self.ofd.write(f"@{label}_END\n")
        self.ofd.write("0;JMP\n")
        self.ofd.write(f"({label}_TRUE)\n")
        self.ofd.write("@SP\n")
        self.ofd.write("A=M\n")
        self.ofd.write("M=-1\n")
        self.ofd.write(f"({label}_END)\n")
        self.ofd.write("@SP\n")
        self.ofd.write("M=M+1\n")

    def op_and(self):
        self.ofd.write("// and\n")
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n") #pop y
        self.ofd.write("D=M\n") # D = y
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n") # pop x
        self.ofd.write("M=D&M\n") # M = x and y
        self.ofd.write("@SP\n")
        self.ofd.write("M=M+1\n")

    def op_or(self):
        self.ofd.write("// or\n")
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")
        self.ofd.write("D=M\n")
        self.ofd.write("@SP\n")
        self.ofd.write("AM=M-1\n")
        self.ofd.write("M=D|M\n") # M = x or y
        self.ofd.write("@SP\n")
        self.ofd.write("M=M+1\n")

    def op_not(self):
        self.ofd.write("// not\n")
        self.ofd.write("@SP\n")
        self.ofd.write("A=M-1\n")
        self.ofd.write("M=!M\n") #Not on the top value


class VMTranslator:
    def __init__(self, input_file):
        self.input_file = input_file
        self.output_file = input_file.replace(".vm", ".asm")
        self.code_writer = CodeWriter(self.output_file)

    def translate(self):
        print(f"Translating {self.input_file} into {self.output_file}")

        with open(self.input_file, "r") as ifd:
            for line in ifd.readlines():
                line = line.strip() #remove whitespaces
                if not line or line.startswith("//"): # check and skip empty lines
                    continue
                print(f"Processing line: {line}")

                words = line.split() #split line into words
                op = words[0] # first word is operation
                args = words[1:]

                match op:
                    case 'push':
                        self.code_writer.op_push(args[0], args[1])
                    case 'pop':
                        self.code_writer.op_pop(args[0], args[1])
                    case 'add':
                        self.code_writer.op_add()
                    case 'sub':
                        self.code_writer.op_sub()
                    case 'neg':
                        self.code_writer.op_neg()
                    case 'eq':
                        self.code_writer.op_eq()
                    case 'gt':
                        self.code_writer.op_gt()
                    case 'lt':
                        self.code_writer.op_lt()
                    case 'and':
                        self.code_writer.op_and()
                    case 'or':
                        self.code_writer.op_or()
                    case 'not':
                        self.code_writer.op_not()
                    case _:
                        raise Exception(f"Unexpected operation {op}")

        self.code_writer.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 vm-to-asm.py <input_file>")
        sys.exit(1)

    vm_translator = VMTranslator(sys.argv[1])
    vm_translator.translate()
