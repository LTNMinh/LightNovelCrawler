import sys 

def print_progress(index, total):
    print(f"Progress {int((index + 1) / total * 100)}%")
    sys.stdout.flush()