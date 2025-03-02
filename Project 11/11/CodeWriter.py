class CodeWriter:
    def __init__(self, output_file):
        self.pop_written = False
        self.file_name = None
        self.output_file = output_file
        self.label_counter = 0
        self.vm_output = []
        self.pending_pop_temp = False


    def set_file_name(self, file_name):
        self.file_name = file_name

    def write_arithmetic(self, command):
        valid_commands = ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]
        if command in valid_commands:
            self.write_vm_command(command)
            print(f"DEBUG: CodeWriter is writing arithmetic command '{command}'.")
        else:
            raise ValueError(f"Unknown arithmetic command: {command}")

    def write_push(self, segment, index):
        if segment is None or index is None:
            print(f"ERROR: Attempted to push with None value. segment: {segment}, index: {index}")
            return
        command = f"push {segment} {index}"
        self.write_vm_command(command)

    def write_pop(self, segment, index):
        if segment is None or index is None:
            print(f"ERROR: Attempted to push with None value. segment: {segment}, index: {index}")
            return
        command = f"pop {segment} {index}"
        self.write_vm_command(command)

    def write_push_string(self, string_value):
        if string_value is None:
            print("ERROR: Attempted to write None value to string push.")
            return

        print(f"DEBUG: Writing VM commands to push string: '{string_value}'")
        self.write_push('constant', len(string_value))
        self.write_call('String.new', 1)

        for char in string_value:
            self.write_push('constant', ord(char))  # Get ASCII value of character
            self.write_call('String.appendChar', 2)

    def write_label(self, label):
        self.write_vm_command(f"label {label}")

    def write_goto(self, label):
        self.write_vm_command(f"goto {label}")

    def write_if(self, label):
        self.write_vm_command(f"if-goto {label}")

    def write_call(self, name, n_args):
        if name is None or n_args is None:
            print(f"ERROR: Invalid name or arguments in write_call.")
            return

        command = f"call {name} {n_args}"
        print(f"DEBUG: Writing VM command: {command}")
        self.write_vm_command(command)

        if name.startswith("Output.print") and "Math." not in name:
            self.pending_pop_temp = True
        else:
            self.pending_pop_temp = False

    def finalize_pop(self):
        if self.pending_pop_temp:
            self.write_vm_command("pop temp 0")
            self.pending_pop_temp = False

    def write_function(self, function_name, n_locals):
        command = f"function {function_name} {n_locals}"
        self.write_vm_command(command)

    def write_return(self):
        self.write_vm_command("return")

    def write_command(self, commands):
        for command in commands:
            self.write_vm_command(command)

    def write_vm_command(self, command):
        if command is None:
            print("ERROR: Attempted to write a None command to VM output")
            return
        print(f"DEBUG: Writing VM command: {command}")
        self.vm_output.append(command)

    def close(self):
        with open(self.output_file, 'w') as file:
            for command in self.vm_output:
                file.write(command + '\n')
