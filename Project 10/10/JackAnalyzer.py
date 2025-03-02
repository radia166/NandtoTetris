import os
import sys



def main(argv: list[str]):
    targets = []
    sourceDir = argv[0]

    # Ensure we only attempt to compile a jack file
    if os.path.isfile(sourceDir):
        if not sourceDir.endswith('.jack'):
            print(f'Target {sourceDir} is not a valid source file')
            return
        targets.append(sourceDir)

    if os.path.isdir(sourceDir):
        files = os.listdir(sourceDir)
        jackFiles = [os.path.join(sourceDir, file) for file in files if file.endswith('.jack')]
        if not jackFiles:
            print(f'Folder {sourceDir} does not contain any jack files')
            return
        targets.extend(jackFiles)

    print(f'Parsing {len(targets)} targets')
    for target in targets:
        print(f'Parsing {target}')
        # Add your code here
        print(f'{target} parsed successfully')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} [source]')
        exit()
    main(sys.argv[1:])
