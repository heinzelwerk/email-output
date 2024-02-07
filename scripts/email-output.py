#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import sys


class Program:
    @staticmethod
    def _setup_argparser():
        kwargs = {}
        parser = argparse.ArgumentParser(**kwargs)
        return parser

    def _parse_args(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]

        return self._argparser.parse_args(argv)

    def __init__(self):
        self._argparser = self._setup_argparser()

    def __call__(self, *args, **kwargs):
        argv = kwargs.get('argv', None)
        cmd_args = self._parse_args(argv)
        print(cmd_args)
        return os.EX_OK


def main(*args, **kwargs):
    program = Program()
    exitval = program(*args, **kwargs)
    sys.exit(exitval)


if __name__ == '__main__':
    main()
