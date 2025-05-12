import sys
import os

def print_debug_info():
    print("Python Version:", sys.version)
    print("\nCurrent Directory:", os.getcwd())
    print("\nDirectory Contents:")
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")

    print("\nEnvironment Variables:")
    for key, value in os.environ.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    print_debug_info()
