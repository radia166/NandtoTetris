import os
import platform

windows = platform.system() == 'Windows'
executable = 'python' if windows else 'python3'
scriptExt = 'bat' if windows else 'sh'

def main(entrypoint = 'JackAnalyzer.py'):
    """
    Expects the parsed files to be in the same directory.

    Calls JackAnalyzer.py with each folder in the project directory and
    checks that the output matches with the reference.

    Your assignment should write each output file e.g. MainT.xml and Main.xml
    in the project directory, not the program directory
    """

    folders = [entry for entry in os.listdir() if os.path.isdir(entry) and 'pycache' not in entry]
    results = []
    cmd = os.path.join('..', '..', 'tools', f'TextComparer.{scriptExt}')

    for folder in folders:
        print('*' * 80)
        print(f'Testing folder {folder}')
        code = os.system(f'{executable} {entrypoint} {folder}')
        if code != 0:
            print(f'Analyzer failed on {folder}')

        names = [entry.replace('.jack', '') for entry in os.listdir(folder) if entry.endswith('.jack')]
        for name in names:
            tokens = f'{name}T.xml'
            parsed = f'{name}.xml'
            if not os.path.exists(tokens):
                print('Missing tokenized output')
            if not os.path.exists(parsed):
                print('Missing parse output')

            tokensRef = os.path.join(folder, tokens)
            parsedRef = os.path.join(folder, parsed)

            print(f'Comparing {tokens} with {tokensRef}')
            code = os.system(f'{"" if windows else "sh "}{cmd} {tokens} {tokensRef}')
            results.append((tokensRef, code))

            print(f'Comparing {parsed} with {parsedRef}')
            code = os.system(f'{"" if windows else "sh "}{cmd} {parsed} {parsedRef}')
            results.append((parsedRef, code))

    print('\n' + '=' * 36 + 'SUMMARY' + '=' * 37 + '\n')

    passed = 0
    for program, result in results:
        print(f'{program:<40}: ', end="")
        if result == 0:
            print("passed")
            passed += 1
        else:
            print("failed")

    print(f'\nPassed {passed} of {len(results)}')
    # TODO: Grading formula
    print(f'Estimated grade {int(max(0, (passed - 2)/4))}')
    print('\nThe actual grade for the project is assessed by the course lecturer after inspecting your solution')

if __name__ == "__main__":
    main()
