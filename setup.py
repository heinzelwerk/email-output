#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages


def long_description():
    path = os.path.abspath(os.path.dirname(__file__))
    file = os.path.join(path, 'README.rst')
    with open(file) as f:
        return f.read()


setup(
    name='email-output',
    version='1.0.dev0',
    description='Execute a command and send its output via email',
    long_description=long_description(),
    long_description_content_type='text/x-rst',
    url='https://dev.heinzelwerk.de/git/python/email-output',
    author='Jens Kleineheismann',
    author_email='heinzel@farbemachtstark.de',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: Public Domain',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    python_requires='>=3',
    scripts=['scripts/email-output.py'],
)
