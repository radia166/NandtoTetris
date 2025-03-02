import sys
import os
import glob
from pathlib import Path

class CodeWriter:
    def __init__(self, output_file):
        self.file_name = None
        self.label_counter = 0
        self.output_file_name = output_file
        self.ofd = open(output_file, 'w')
        self.labels = {}
        self.base_fn = "bootstrap"

    def set_file_name(self, file_name):
        self.file_name = Path(file_name).stem  # Set the file name for static variables
        self.base_fn = self.file_name  # Use file name as base for label replacement

    def new_label(self, label):
        if label in self.labels:
            self.labels[label] += 1
        else:
            self.labels[label] = 1

    def replace_labels(self, s):
        for label in self.labels:
            s = s.replace(f"<{label}>", f"{label}{self.labels[label]}")
        s = s.replace("<FILENAME>", self.base_fn)
        return s

    def emit(self, code_line):
        code_line = self.replace_labels(code_line)  # Replace placeholders
        self.ofd.write(code_line + '\n')

    def emit_comment(self, comment):
        comment = self.replace_labels(comment)
        self.ofd.write(f"// {comment}\n")

    def close(self):
        print(f"Closing file: {self.ofd.name}")
        self.ofd.close()

    def __exit__(self, *args):
        self.close()

    def op_push(self, memorysegment, index):
        segment_map = {
            "local": "LCL",
            "argument": "ARG",
            "this": "THIS",
            "that": "THAT",
            "temp": "R5"  # temp starts at R5
        }

        self.emit_comment(f"push {memorysegment} {index}")

        if memorysegment == "constant":
            self.emit(f"@{index}")
            self.emit("D=A")  # D=constant value
            self.emit("@SP")
            self.emit("A=M")
            self.emit("M=D")  # push value onto stack
            self.emit("@SP")
            self.emit("M=M+1 \n")

        elif memorysegment in segment_map:
            self.emit(f"@{segment_map[memorysegment]}")
            self.emit("D=M")  # D = base address of the segment
            self.emit(f"@{index}")
            self.emit("A=D+A")
            self.emit("D=M")
            self.emit("@SP")
            self.emit("A=M")
            self.emit("M=D")   # push value onto stack
            self.emit("@SP")
            self.emit("M=M+1 \n")

        elif memorysegment == "temp":
            self.emit(f"@{5 + int(index)}")  # temp segment starts at R5
            self.emit("D=M")
            self.emit("@SP")
            self.emit("A=M")
            self.emit("M=D")
            self.emit("@SP")
            self.emit("M=M+1 \n")

        elif memorysegment == "static":
            self.emit(f"// push static {index}")
            self.emit(f"@{self.file_name}.{index}")
            self.emit("D=M")
            self.emit("@SP")
            self.emit("A=M")
            self.emit("M=D")
            self.emit("@SP")
            self.emit("M=M+1 \n")

        elif memorysegment == "pointer":
            self.emit(f"// push pointer {index}")
            if index == "0":
                self.emit("@THIS")
            elif index == "1":
                self.emit("@THAT")
            self.emit("D=M")
            self.emit("@SP")
            self.emit("A=M")
            self.emit("M=D")
            self.emit("@SP")
            self.emit("M=M+1 \n")

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
        self.emit_comment(f"pop {memorysegment} {index}")

        if memorysegment in segment_map:
            self.emit(f"@{index}")
            self.emit("D=A")
            self.emit(f"@{segment_map[memorysegment]}")
            if memorysegment != "temp":
                self.emit("D=D+M \n")
            else:
                self.emit("D=D+A")
            self.emit("@R13")
            self.emit("M=D")  #store base+index in R13
            self.emit("@SP")
            self.emit("AM=M-1")
            self.emit("D=M")
            self.emit("@R13")
            self.emit("A=M")  # A = base + index
            self.emit("M=D \n")

        elif memorysegment == "static":
            self.emit(f"// pop static {index}")
            self.emit("@SP")
            self.emit("AM=M-1")  #pop the top value
            self.emit("D=M")  #popped value in D
            self.emit(f"@{self.file_name}.{index}")
            self.emit("M=D \n")  # pop static[index]

        elif memorysegment == "pointer":
            self.emit(f"// pop pointer {index}")
            self.emit("@SP")
            self.emit("AM=M-1")
            self.emit("D=M")
            if index == "0":
                self.emit("@THIS")  #THIS = 0
            elif index == "1":
                self.emit("@THAT")  #THAT = 1
            self.emit("M=D \n")

        else:
            raise Exception(f"Unknown memory segment: {memorysegment}")

#functions
    def op_function(self, function_name, n_vars):
        self.emit_comment(f"function {function_name} {n_vars} \n")
        self.emit(f"({function_name}) \n")  #declare function label
        for _ in range(int(n_vars)):
            self.emit("@SP")
            self.emit("A=M") #get address at sp
            self.emit("M=0") # set that address to 0
            self.emit("@SP") # update sp
            self.emit("M=M+1") #sp++

    def op_goto(self, label):
        self.emit_comment(f"goto {label} ")
        self.emit(f"@{label}")
        self.emit("0;JMP \n") #jump unconditional

    def op_if_goto(self, label):
        self.emit_comment(f"if-goto {label} ")
        self.emit("@SP")
        self.emit("AM=M-1")
        self.emit("D=M")
        self.emit(f"@{label}")  #loading address of label
        self.emit("D;JNE \n")  #jump to label if D!=0

    def op_call(self, function_name, n_args):
        return_label = f"RETURN_{self.label_counter}"
        self.label_counter += 1
        self.emit_comment(f"call {function_name} {n_args}")
        # push return address to stack
        self.emit(f"@{return_label}")
        self.emit("D=A") # D =return address
        self.emit("@SP")
        self.emit("A=M") # A = sp value
        self.emit("M=D") #store ret-address at top of stack
        self.emit("@SP")
        self.emit("M=M+1")
        # push lcl
        self.emit("@LCL")
        self.emit("D=M") # D= current lcl value
        self.emit("@SP")
        self.emit("A=M") # A = sp value
        self.emit("M=D") #store lcl at top of stack
        self.emit("@SP")
        self.emit("M=M+1")
        # push agr onto stack
        self.emit("@ARG")
        self.emit("D=M")
        self.emit("@SP")
        self.emit("A=M")
        self.emit("M=D") #store arg on top of stack
        self.emit("@SP")
        self.emit("M=M+1")
        # push this onto stack
        self.emit("@THIS")
        self.emit("D=M") #D= current this value
        self.emit("@SP")
        self.emit("A=M")
        self.emit("M=D")
        self.emit("@SP")
        self.emit("M=M+1")
        # push that onto stack
        self.emit("@THAT")
        self.emit("D=M")#D= current that value
        self.emit("@SP")
        self.emit("A=M")
        self.emit("M=D")
        self.emit("@SP")
        self.emit("M=M+1")

        self.emit("@SP")
        self.emit("D=M") # D = SP
        self.emit(f"@{int(n_args) + 5}") #converting n_args to int before adding
        self.emit("D=D-A") # D = SP - (n_args + 5)
        self.emit("@ARG")
        self.emit("M=D") #set arg to sp - (n_args + 5)

        self.emit("@SP")  #lcl = sp
        self.emit("D=M")
        self.emit("@LCL")
        self.emit("M=D") #set lcl to sp
        self.emit(f"@{function_name}")
        self.emit("0;JMP") # jump to function
        self.emit(f"({return_label}) \n")  #return label

    def op_return(self):
        self.emit_comment("return")
        self.emit("@LCL") #Store lcl as frame)
        self.emit("D=M")
        self.emit("@R13")  #store frame in R13
        self.emit("M=D")

        self.emit("@5") #load 5 to get return address stored at FRAME - 5
        self.emit("A=D-A") #now  A = frame - 5
        self.emit("D=M")
        self.emit("@R14")  # store return address in R14
        self.emit("M=D")

        self.emit("@SP")
        self.emit("AM=M-1")  # sp--
        self.emit("D=M")
        self.emit("@ARG")
        self.emit("A=M")
        self.emit("M=D")  #arg* = pop()

        self.emit("@ARG")
        self.emit("D=M+1") # D = arg + 1
        self.emit("@SP")
        self.emit("M=D")

        self.emit("@R13")
        self.emit("D=M")
        self.emit("@1")
        self.emit("A=D-A") # frame - 1
        self.emit("D=M")
        self.emit("@THAT") #restore that
        self.emit("M=D") # that = * frame-1

        self.emit("@R13")
        self.emit("D=M")
        self.emit("@2")
        self.emit("A=D-A") # A= frame - 2
        self.emit("D=M")
        self.emit("@THIS") #restore this
        self.emit("M=D") # this = * frame-2

        self.emit("@R13")
        self.emit("D=M")
        self.emit("@3")
        self.emit("A=D-A") #A = frame -3
        self.emit("D=M")
        self.emit("@ARG") #restore arg
        self.emit("M=D") # arg = * frame-3

        self.emit("@R13")
        self.emit("D=M")
        self.emit("@4")
        self.emit("A=D-A") # A = frame - 4
        self.emit("D=M")
        self.emit("@LCL")
        self.emit("M=D")# lcl = * frame - 4

        self.emit("@R14")
        self.emit("A=M")
        self.emit("0;JMP \n")

    def op_arithmetic(self, command):  # dispatcher
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
        self.emit("//add")
        self.emit("@SP")
        self.emit("AM=M-1")
        self.emit("D=M")  #Store y in D
        self.emit("@SP")
        self.emit("AM=M-1")
        self.emit("M=D+M") # x = x + y
        self.emit("@SP")
        self.emit("M=M+1 \n")

    def op_sub(self):
        self.emit("// sub")
        self.emit("@SP")
        self.emit("AM=M-1")  #pop y
        self.emit("D=M")  # D = y
        self.emit("@SP")
        self.emit("AM=M-1")  # pop x
        self.emit("M=M-D")  # x = x - y
        self.emit("@SP")
        self.emit("M=M+1 \n")

    def op_neg(self):
        self.emit("// neg ")
        self.emit("@SP")
        self.emit("A=M-1")
        self.emit("M=-M \n")  # Neg top value

    def op_eq(self):
        self.label_counter += 1
        label = f"EQ_{self.label_counter}"
        self.emit(f"// eq")
        self.emit("@SP")
        self.emit("AM=M-1")  #pop y
        self.emit("D=M")  # D = y
        self.emit("@SP")
        self.emit("AM=M-1")  #pop x
        self.emit("D=M-D")  # D = x - y
        self.emit(f"@{label}_TRUE")
        self.emit("D;JEQ")  # Jump to EQ_TRUE, if x == y
        self.emit("@SP")
        self.emit("A=M")
        self.emit("M=0")  #False (0)
        self.emit(f"@{label}_END")
        self.emit("0;JMP")  # Jump to EQ_END
        self.emit(f"({label}_TRUE)")
        self.emit("@SP")
        self.emit("A=M")
        self.emit("M=-1")  #True (-1)
        self.emit(f"({label}_END)")
        self.emit("@SP")
        self.emit("M=M+1 \n")

    def op_lt(self):
        self.label_counter += 1
        label = f"LT_{self.label_counter}"
        self.emit(f"// lt")
        self.emit("@SP")
        self.emit("AM=M-1")  #pop y
        self.emit("D=M")
        self.emit("@SP")
        self.emit("AM=M-1")  #pop x
        self.emit("D=M-D")  # D = x - y
        self.emit(f"@{label}_TRUE")
        self.emit("D;JLT")  # Jump to LT_TRUE, if x < y
        self.emit("@SP")
        self.emit("A=M")
        self.emit("M=0")  # False (0)
        self.emit(f"@{label}_END")
        self.emit("0;JMP")
        self.emit(f"({label}_TRUE)")
        self.emit("@SP")
        self.emit("A=M")
        self.emit("M=-1")  # True (-1)
        self.emit(f"({label}_END)")
        self.emit("@SP")
        self.emit("M=M+1 \n")

    def op_gt(self):
        self.label_counter += 1
        label = f"GT_{self.label_counter}"
        self.emit(f"// gt")
        self.emit("@SP")
        self.emit("AM=M-1")
        self.emit("D=M")  # D = y
        self.emit("@SP")
        self.emit("AM=M-1")
        self.emit("D=M-D")  # D = x - y
        self.emit(f"@{label}_TRUE")
        self.emit("D;JGT")  # Jump to GT_TRUE,if x > y
        self.emit("@SP")
        self.emit("A=M")
        self.emit("M=0")
        self.emit(f"@{label}_END")
        self.emit("0;JMP")
        self.emit(f"({label}_TRUE)")
        self.emit("@SP")
        self.emit("A=M")
        self.emit("M=-1")
        self.emit(f"({label}_END)")
        self.emit("@SP")
        self.emit("M=M+1 \n")

    def op_and(self):
        self.emit("// and")
        self.emit("@SP")
        self.emit("AM=M-1") #pop y
        self.emit("D=M") # D = y
        self.emit("@SP")
        self.emit("AM=M-1") # pop x
        self.emit("M=D&M") # M = x and y
        self.emit("@SP")
        self.emit("M=M+1 \n")

    def op_or(self):
        self.emit("// or")
        self.emit("@SP")
        self.emit("AM=M-1")
        self.emit("D=M")
        self.emit("@SP")
        self.emit("AM=M-1")
        self.emit("M=D|M") # M = x or y
        self.emit("@SP")
        self.emit("M=M+1 \n")

    def op_not(self):
        self.emit("// not ")
        self.emit("@SP")
        self.emit("A=M-1")
        self.emit("M=!M \n") #Not on the top value

    def op_label(self, label):
        self.emit(f"({label})")


class VMTranslator:
    def __init__(self, input_file):
        self.input_path = input_file
        if os.path.isdir(input_file):  # if multiple files/directory
            self.output_file = os.path.join(input_file, os.path.basename(input_file)) + ".asm"
        else:
            self.output_file = input_file.replace(".vm", ".asm")  # for single file
        self.code_writer = CodeWriter(self.output_file)

    def bootstrap_code(self):    #for sys.vm
        self.code_writer.emit_comment("Bootstrap code\n")
        self.code_writer.emit("@256")  #initialize sp @256
        self.code_writer.emit("D=A")
        self.code_writer.emit("@SP")
        self.code_writer.emit("M=D") #sp =256
        self.code_writer.emit_comment("Call Sys.init\n") #call sys on 0 arg
        self.code_writer.emit("@RETURN_BOOTSTRAP")

        self.code_writer.emit("D=A")
        self.code_writer.emit("@SP")
        self.code_writer.emit("A=M")
        self.code_writer.emit("M=D") #storing D on top of the stack
        self.code_writer.emit("@SP")
        self.code_writer.emit("M=M+1\n") #sp++

        # Pushing lcl
        self.code_writer.emit("@0") #lcl 0 initially
        self.code_writer.emit("D=A")
        self.code_writer.emit("@SP")
        self.code_writer.emit("A=M")
        self.code_writer.emit("M=D") #push lcl
        self.code_writer.emit("@SP")
        self.code_writer.emit("M=M+1\n") #sp++

        # Pushing arg
        self.code_writer.emit("@0") #arg start as 0
        self.code_writer.emit("D=A")
        self.code_writer.emit("@SP")
        self.code_writer.emit("A=M")
        self.code_writer.emit("M=D") #push arg
        self.code_writer.emit("@SP")
        self.code_writer.emit("M=M+1\n") #sp++

        #Pushing this
        self.code_writer.emit("@0")
        self.code_writer.emit("D=A")
        self.code_writer.emit("@SP")
        self.code_writer.emit("A=M")
        self.code_writer.emit("M=D") #push this
        self.code_writer.emit("@SP")
        self.code_writer.emit("M=M+1\n")

        #Pushing that
        self.code_writer.emit("@0") # srart 0
        self.code_writer.emit("D=A")
        self.code_writer.emit("@SP")
        self.code_writer.emit("A=M")
        self.code_writer.emit("M=D") #push that
        self.code_writer.emit("@SP")
        self.code_writer.emit("M=M+1\n")

        #setting arg pointer to sp-5
        self.code_writer.emit("@SP")
        self.code_writer.emit("D=M")
        self.code_writer.emit("@5")
        self.code_writer.emit("D=D-A")
        self.code_writer.emit("@ARG")
        self.code_writer.emit("M=D\n") #arg = sp - 5

        #setting lcl=sp
        self.code_writer.emit("@SP")
        self.code_writer.emit("D=M")
        self.code_writer.emit("@LCL")
        self.code_writer.emit("M=D\n") #lcl = sp
        self.code_writer.emit("@Sys.init") #set up and call Sys.init
        self.code_writer.emit("0;JMP")

        self.code_writer.emit("(RETURN_BOOTSTRAP)\n")


    def translate(self):
        if os.path.isdir(self.input_path):  # for multiple files/directory
            vm_files = glob.glob(os.path.join(self.input_path, "*.vm"))
            if any("sys.vm" in vm_file.lower() for vm_file in vm_files):  # Add bootstrap if sys.vm exists
                self.bootstrap_code()
            for vm_file in vm_files:
                self.process_vm_file(vm_file)
        else:
            self.process_vm_file(self.input_path)
        self.code_writer.close()

    def process_vm_file(self, vm_file):
        if os.path.isfile(vm_file):
            print(f"Translating {vm_file} into {self.output_file}")
            self.code_writer.set_file_name(vm_file)

            with open(vm_file, "r") as ifd:  #changed from self.input_path to vm_file
                for line in ifd.readlines():
                    line = line.strip()  # remove whitespaces
                    if not line or line.startswith("//"):  # check and skip empty lines
                        continue
                    print(f"Processing line: {line}")
                    words = line.split()  # split line into words
                    op = words[0]  # first word is operation
                    args = words[1:]
                    self.handle_operation(op, args)

    def handle_operation(self, op, args):
        match op:
            case 'push':
                self.code_writer.op_push(args[0], args[1])
            case 'pop':
                self.code_writer.op_pop(args[0], args[1])
            case 'label':
                self.code_writer.op_label(args[0])
            case 'goto':
                self.code_writer.op_goto(args[0])
            case 'if-goto':
                self.code_writer.op_if_goto(args[0])
            case 'function':
                self.code_writer.op_function(args[0], args[1])
            case 'call':
                self.code_writer.op_call(args[0], args[1])
            case 'return':
                self.code_writer.op_return()
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


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 vm-to-asm.py <input_directory_or_file>")
        sys.exit(1)

    vm_translator = VMTranslator(sys.argv[1])
    vm_translator.translate()

