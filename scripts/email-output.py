#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import subprocess
import sys

PROG_NAME = 'email-output.py'
VERSION = '1.0'


class Program:
    @staticmethod
    def _setup_argparser():
        kwargs = {
            'prog': PROG_NAME,
            'description': 'Execute a command and send its output via email',
            'usage': 'usage: %(prog)s [OPTIONS] [--] COMMAND [ARGS ...]',
            'epilog': 'To prevent ARGS to be interpreted as OPTIONS to %(prog)s, add two dashes (--) before the COMMAND.'
        }
        parser = argparse.ArgumentParser(**kwargs)
        parser.add_argument('-V', '--version', action='version', version='%(prog)s {}'.format(VERSION))
        parser.add_argument('-C', '--no-combined',
                            action='store_true',
                            help='do not combine stdout and stderr')
        parser.add_argument('-E', '--no-empty',
                            action='store_true',
                            help='do not send an email, if no output was produced')
        parser.add_argument('-r', '--recipient', nargs=1, metavar='ADDR',
                            action='append',
                            help='the email address, that the command output will be sent to')
        parser.add_argument('command', nargs=1, metavar='COMMAND',
                            help='the command, that will be executed')
        parser.add_argument('argv', nargs='*', metavar='ARGS',
                            help='arguments to COMMAND')
        return parser

    def _parse_args(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]

        return self._argparser.parse_args(argv)

    def __init__(self):
        self._argparser = self._setup_argparser()

    def __call__(self, *args, **kwargs):
        argv = kwargs.get('argv', None)
        prog_args = self._parse_args(argv)
        cmd = prog_args.command + prog_args.argv
        if prog_args.no_combined:
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE
        else:
            stdout = subprocess.PIPE
            stderr = subprocess.STDOUT
        ret = subprocess.run(cmd, stdout=stdout, stderr=stderr)
        if ret.stdout:
            sys.stdout.write(ret.stdout.decode(sys.stdout.encoding))
        if ret.stderr:
            sys.stderr.write(ret.stderr.decode(sys.stderr.encoding))
        exitval = ret.returncode
        return exitval


def main(*args, **kwargs):
    program = Program()
    exitval = program(*args, **kwargs)
    sys.exit(exitval)


if __name__ == '__main__':
    main()
