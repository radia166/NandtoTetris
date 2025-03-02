import os, platform

dirs = [
    'FunctionCalls',
    'ProgramFlow'
]

programs = []
for dir in dirs:
    children = os.listdir(dir)
    for child in children:
        path = os.path.join(dir, child)
        if os.path.isdir(path):
            programs.append(path)

results = []

if platform.system() == "Windows":
    python_exec="python"
else:
    python_exec="python3"

for program in programs:
    name = program.split('/')[1]

    print('*' * 80)
    print(f'Running test: {program}')

    # Run translator
    cmd = f'{python_exec} vm-to-asm.py {program}'
    print(f'Running command: {cmd}')
    os.system(cmd)

    # Run emulator
    test = os.path.join(program, name)
    if platform.system() == 'Windows':
        cmd = f'..\\..\\tools\\CPUEmulator.bat {test}.tst'
    else:
        cmd = f'sh ../../tools/CPUEmulator.sh {test}.tst'
    print(f'Executing command: {cmd}')
    results.append(os.system(cmd))
    print()

passed = 0
print('Summary\n')
for test, result in zip(programs, results):
    print('%-30s' % test, end=": ")
    if result == 0:
        print('passed')
        passed += 1
    else:
        print('failed')

print(f'\nPassed {passed} of {len(results)}')
print(f'Estimated grade {max(0, passed - 2)}')
print('\nThe actual grade for the project is assesed by the course instruction after inspecting your solution')