#!/usr/bin/env python3

import shlex
import shutil
import os
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


def handle_source_file(filename):
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
        return './a.out'
    else:
        return filename


SIZES = ('128M', '256M', '512M', '1G', '2G', '4G', '8G')

UNITS = {'K': 1024, 'M': 1024**2, 'G': 1024**3}


def get_int_count(size_with_units):
    size_with_units = size_with_units.strip().upper()
    if size_with_units == '8G':
        # this is a special case to fit C's 32 bit signed integer
        return 2147483647
    try:
        if size_with_units.endswith(tuple(UNITS)):
            value, unit = size_with_units[:-1], size_with_units[-1]
            return int(value) * UNITS[unit] // 4
        else:
            if int(size_with_units) % 4:
                raise SystemExit('{} is not a multiple of sizeof(int)'.format(
                    size_with_units))
            return int(size_with_units) // 4
    except ValueError:
        raise SystemExit('{} is not a valid size'.format(size_with_units))


def bench(filename, timeout, nps, sizes):
    if os.path.exists('_bench_output'):
        try:
            input(
                '_bench_output/ exists, [Enter] to remove or [Ctrl+C] to abort')
        except KeyboardInterrupt:
            print()
            raise SystemExit(1)
        shutil.rmtree('_bench_output')
    os.mkdir('_bench_output')

    show_mpi()
    print('output file, stdout, stderr will be stored at _bench_output/')

    datasizes = [get_int_count(size) for size in sizes]

    executable = handle_source_file(filename)

    if not os.path.exists(executable):
        raise SystemExit('The executable {!r} does not exist'.format(
            executable))

    summary = []
    header = 'size  {}'.format('  '.join('np={}'.format(np).rjust(6)
                                         for np in nps))

    if not os.path.isdir('testcase_benchmark'):
        os.mkdir('testcase_benchmark')

    print('=' * 79)

    try:
        for size, datasize in zip(sizes, datasizes):
            input_file = 'testcase_benchmark/testcase_{}'.format(size)
            if not os.path.exists(input_file) or os.stat(
                    input_file).st_size != datasize * 4:
                mrtcmd = [
                    'reference/make_random_testcase', input_file, str(datasize)
                ]
                print_command(mrtcmd)
                subprocess.run(mrtcmd, check=True)

            sorted_file = 'testcase_benchmark/sorted_{}'.format(size)
            if not os.path.exists(sorted_file) or os.stat(
                    sorted_file).st_size != datasize * 4:
                refsolcmd = [
                    'reference/gcc_parallel_sort', str(datasize),
                    str(input_file), str(sorted_file)
                ]
                print_command(refsolcmd)
                subprocess.run(refsolcmd, check=True)

            exectime = []
            summary.append((size, exectime))
            for np in nps:
                output_file = '_bench_output/{}_{}_output'.format(size, np)
                print(
                    end='size={:<5}  np={:<3}  '.format(size, np), flush=True)
                command = list(
                    map(str, ('mpirun', '-np', str(
                        np), '-hostfile', 'hostfile', executable, datasize,
                              input_file, output_file)))
                start_time = time.perf_counter()
                try:
                    with open(
                            '_bench_output/{}_{}_stdout'.format(size, np),
                            'wb') as stdout, open(
                                '_bench_output/{}_{}_stderr'.format(size, np),
                                'wb') as stderr:
                        subprocess.run(command,
                                       check=True,
                                       start_new_session=True,
                                       timeout=timeout,
                                       stdout=stdout,
                                       stderr=stderr)
                except subprocess.TimeoutExpired:
                    verdict = red('Timed Out')
                    short = red('TLE'.rjust(6))
                except subprocess.CalledProcessError:
                    verdict = red('Runtime Error')
                    short = red('RE'.rjust(6))
                else:
                    try:
                        cmp = filecmp.cmp(output_file,
                                          sorted_file,
                                          shallow=False)
                    except FileNotFoundError:
                        verdict = red('No Output')
                        short = red('NO'.rjust(6))
                    else:
                        if cmp:
                            verdict = green('Accepted')
                            short = None
                        else:
                            verdict = red('Wrong Answer')
                            short = red('WA'.rjust(6))
                finally:
                    end_time = time.perf_counter()
                print('{:24}  {:6.3f}'.format(verdict, end_time - start_time))
                if short is None:
                    short = format(end_time - start_time, '6.3f')
                else:
                    print_command(command)
                exectime.append(short)
    except KeyboardInterrupt:
        print()

    print('=' * 79)
    print(header)
    print('-' * 79)
    for size, exectime in summary:
        print('{:>4}  {}'.format(size, '  '.join(exectime)))
    print('=' * 79)

    show_mpi()
    print('filename =', filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('filename', help='path to executable or source file')
    parser.add_argument(
        '--timeout', type=float, default=60., help='timeout on each test')
    parser.add_argument(
        '--np',
        type=int,
        nargs='+',
        default=[1, 2, 4, 8, 16, 32],
        help='number of processes')
    parser.add_argument(
        '--size', nargs='+', default=SIZES, help='input size, in K, M, or G')
    args = parser.parse_args()
    bench(args.filename, args.timeout, args.np, args.size)
