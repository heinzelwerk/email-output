#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import subprocess
from setuptools import setup

MAIN_SCRIPT = 'email-output.py'


def version():
    path = os.path.abspath(os.path.dirname(__file__))
    script = os.path.join(path, MAIN_SCRIPT)
    try:
        ret = subprocess.run([script, '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, check=True)
        output = ret.stdout
    except subprocess.CalledProcessError:
        output = 'bogus 0.1.dev0'
    return re.split(r'\s+', output)[1]


def long_description():
    path = os.path.abspath(os.path.dirname(__file__))
    file = os.path.join(path, 'README.rst')
    with open(file) as f:
        return f.read()


setup(
    name='email-output',
    version=version(),
    description='Execute a command and send its output via email',
    long_description=long_description(),
    long_description_content_type='text/x-rst',
    url='https://dev.heinzelwerk.de/git/heinzel/email-output',
    author='Jens Kleineheismann',
    author_email='heinzel@farbemachtstark.de',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: Public Domain',
        'Operating System :: Unix',
        'Programming Language :: Python',
    ],
    python_requires='>=3',
    scripts=[MAIN_SCRIPT],
)
