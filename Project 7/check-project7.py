import os
import platform

tests = [
    "StackArithmetic/StackTest",
    "StackArithmetic/SimpleAdd",
    "MemoryAccess/BasicTest",
    "MemoryAccess/PointerTest",
    "MemoryAccess/StaticTest",
        ]
results = []

if platform.system() == "Windows":
    python_exec="python ..\\..\\"
else:
    python_exec="python3 ../../"


for test in tests:
    file = test.split("/")[1]

    print("*" * 80)
    print("Running test: " + test)
    os.chdir(test)

    # run the VM to assambler translator
    cmd = python_exec+"vm-to-asm.py " + file + ".vm"
    print("Executing command: " + cmd)
    os.system(cmd)

    # run the CPU Emulator from tools.zip to check the solution
    if platform.system() == "Windows":
        cmd = "..\\..\\..\\..\\tools\\CPUEmulator.bat " + file + ".tst"
    else:
        cmd = "sh ../../../../tools/CPUEmulator.sh " + file + ".tst"
    print("Executing command: " + cmd)
    results.append(os.system(cmd))
    if platform.system() == "Windows":
        os.chdir("..\\..")
    else:
        os.chdir("../..")
    print()

passed = 0
print("\nSummary:")
for test, result in zip(tests, results):
    print("%-30s" % test, end=": ")
    if result == 0:
        print("passed")
        passed = passed + 1
    else:
        print("failed")

print("\nPassed", passed, "of", len(results))
print("Estimated grade", max(0, passed - 2))
print("\nThe actual grade for the project is assesed by the course instruction after inspecting your solution")