#!/usr/bin/env python3

import shlex
import shutil
import os
import re
import filecmp
import subprocess
import argparse
import time

* 'Please, be nice and use Python 3.5 or later',


def print_command(command):
    print(' '.join(shlex.quote(arg) for arg in command))


def red(string):
    return '\033[0;31m{}\033[0m'.format(string)


def green(string):
    return '\033[0;32m{}\033[0m'.format(string)


def show_mpi():
    print('mpirun =', shutil.which('mpirun'))


def judge(filename, timeout):
    show_mpi()

    if filename.lower().endswith(('.c', '.cc', '.cpp')):
        if filename.lower().endswith('.c'):
            compileargs = ['mpicc', '-std=gnu99', '-O3', '-Wall', filename]
        else:
            compileargs = ['mpicxx', '-std=gnu++03', '-O3', '-Wall', filename]
        print_command(compileargs)
        try:
            subprocess.run(compileargs, check=True)
        except subprocess.CalledProcessError:
            raise SystemExit('Compilation failed')
        executable = './a.out'
    else:
        executable = filename

    if not os.path.exists(executable):
        raise SystemExit(
            'The executable {!r} does not exist'.format(executable)
        )

    if os.path.exists('_judge_output'):
        shutil.rmtree('_judge_output')
    os.mkdir('_judge_output')

    summary = []

    for i in range(1, 11):
        print('-' * 79)
        input_file = 'testcase/testcase{}'.format(i)
        output_file = '_judge_output/output{}'.format(i)
        sorted_file = 'testcase/sorted{}'.format(i)
        with open('testcase/submit{}.sh'.format(i)) as file:
            submit_script = file.read()
        datasize = int(
            re.search(r'mpiexec \./\$exe (\d+)', submit_script).group(1)
        )
        nodes, ppn = map(
            int,
            re.search(r'PBS -l nodes=(\d+):ppn=(\d+)', submit_script).groups()
        )
        command = list(
            map(
                str, (
                    'mpirun', '-np', str(nodes * ppn), executable, datasize,
                    input_file, output_file
                )
            )
        )
        print_command(command)
        start_time = time.perf_counter()
        try:
            subprocess.run(
                command, check=True, start_new_session=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            verdict = red('Timed Out')
        except subprocess.CalledProcessError as e:
            verdict = red('Runtime Error ({})'.format(e.returncode))
        else:
            try:
                cmp = filecmp.cmp(output_file, sorted_file, shallow=False)
            except FileNotFoundError:
                verdict = red('No Output')
            else:
                if cmp:
                    verdict = green('Accepted')
                else:
                    verdict = red('Wrong Answer')
        finally:
            end_time = time.perf_counter()
        print(
            'testcase{:<2}  {:30}  {:6.3f}'.
            format(i, verdict, end_time - start_time)
        )
        summary.append((i, verdict, end_time - start_time))
    print('=' * 79)
    for i, verdict, duration in summary:
        print(
            'testcase{:<2}  {:30}  {:6.3f}'.format(i, verdict, duration)
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('filename', help='path to executable or source file')
    parser.add_argument(
        '--timeout', type=float, default=60., help='timeout on each test'
    )
    judge(**vars(parser.parse_args()))
