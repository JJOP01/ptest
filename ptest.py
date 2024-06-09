#!/usr/bin/env python3

import sys 
import subprocess
from difflib import unified_diff
from typing import List, BinaryIO, Tuple, Optional 

def read_blob_field(f: BinaryIO, name: bytes) -> bytes:
    line = f.readline()
    field = b':b ' + name + b' '
    assert line.startswith(field), field
    assert line.endswith(b'\n')
    size = int(line[len(field):-1])
    blob = f.read(size)
    assert f.read(1) == b'\n'
    return blob

def read_int_field(f: BinaryIO, name: bytes) -> int:
    line = f.readline()
    field = b':i ' + name + b' '
    assert line.startswith(field)
    assert line.endswith(b'\n')
    return int(line[len(field):-1])

def write_int_field(f: BinaryIO, name: bytes, value: int):
    f.write(b':i %s %d\n' % (name, value))

def write_blob_field(f: BinaryIO, name: bytes, blob: bytes):
    f.write(b':b %s %d\n' % (name, len(blob)))
    f.write(blob)
    f.write(b'\n')

def capture(shell: str) -> dict:
    print(f'Capturing `{shell}`...')
    process = subprocess.run(['sh', '-c', shell], capture_output = True)
    return {
        'shell': shell,
        'stdout': process.stdout,
        'stderr': process.stderr,
        'returncode': process.returncode
    }

def load_list(file_path: str) -> list[str]:
    with open(file_path) as f:
        return [line.strip() for line in f]

def load_snapshots(file_path: str) -> [dict]:
    snapshots = []
    with open(file_path, "rb") as f:
        count = read_int_field(f, b'count')
        for _ in range(count):
            snapshot = {
                'shell': read_blob_field(f, b'shell'),
                'returncode':  read_int_field(f, b'returncode'),
                'stdout': read_blob_field(f, b'stdout'),
                'stderr': read_blob_field(f, b'stderr')
            }
            snapshots.append(snapshot)
    return snapshots

def dump_snapshots(file_path: str, snapshots: list[dict]):
    with open(file_path, "wb") as f:
        write_int_field(f, b"count", len(snapshots))
        for snapshot in snapshots:
            write_blob_field(f, b"shell", bytes(snapshot['shell'], 'utf-8'))
            write_int_field(f, b"returncode", snapshot['returncode'])
            write_blob_field(f, b"stdout", snapshot['stdout'])
            write_blob_field(f, b"stderr", snapshot['stderr'])

if __name__ == "__main__":
    program_name, *argv = sys.argv
    program_name = program_name if "./" in program_name else "ptest"

    if len(argv) == 0:
        print(f'Usage: {program_name} <record|replay> <test.list>')
        print('ERROR: no subcommand is provided')
        exit(1)
    subcommand, *argv = argv

    if subcommand == "record":
        if len(argv) == 0:
            print(f'Usage: {program_name} {subcommand} <test.list>')
            print('ERROR: no test.list is provided')
            exit(1)
        # TODO: read through directory and record/replay files in folder, assert each file is testable
        test_list_path, *argv = argv
        
        snapshots = [capture(shell.strip()) for shell in load_list(test_list_path)]
        dump_snapshots(f'{test_list_path}.bi', snapshots)
    elif subcommand == "replay":
        if len(argv) == 0:
            print(f'Usage: {program_name} {subcommand} <test.list>')
            print('ERROR: no test.list is provided')
            exit(1)
        test_list_path, *argv = argv

        shells = load_list(test_list_path)
        snapshots = load_snapshots(f'{test_list_path}.bi')

        if len(shells) != len(snapshots):
            # TODO: query comparing matching shell commands, show missing tests
            print(f"UNEXPECTED: Amount of shell commands in f{test_list_path}")
            print(f"    EXPECTED: {len(snapshots)}")
            print(f"      ACTUAL: {len(shells)}")
            print(f"NOTE: You may want to do `{program_name} record {test_list_path}` to update {test_list_path}.bi")
            exit(1)
        
        for (shell, snapshot) in zip(shells, snapshots):
            print(f"Replaying `{snapshot['shell']}`")
            snapshot_shell = snapshot['shell'].decode('utf-8')
            if shell != snapshot_shell:
                print(f"UNEXPECTED: shell command")
                print(f"    EXPECTED: {snapshot_shell}")
                print(f"      ACTUAL: {shell}")
                print(f"NOTE: You may want to do `{program_name} record {test_list_path}` to update {test_list_path}.bi")
                exit(1)
            process = subprocess.run(['sh', '-c', snapshot['shell']], capture_output = True)
            running = False
            if process.returncode != snapshot['returncode']:
                print("UNEXPECTED RETURN CODE:")
                print(f"    EXPECTED: {process.returncode}")
                print(f"      ACTUAL: {snapshot['returncode']}")
                running = True
            if process.stdout != snapshot['stdout']:
                a = process.stdout.decode('utf-8').splitlines(keepends=True)
                b = snapshot['stdout'].decode('utf-8').splitlines(keepends=True)
                print("UNEXPECTED STDOUT:")
                for line in unified_diff(a, b):
                    print(line)
                running = True
            if process.stderr != snapshot['stderr']:
                a = process.stderr.decode('utf-8').splitlines(keepends=True)
                b = snapshot['stderr'].decode('utf-8').splitlines(keepends=True)
                print("UNEXPECTED STDERR:")
                for line in unified_diff(a, b):
                    print(line)
            if running:
                exit(1)
        print('\nCompilation output matches recorded output')
    else:
        print(f"ERROR: invalid subcommand '{subcommand}'")
        exit(1)
