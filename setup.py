#  -*- coding: utf-8


from setuptools import find_packages
from setuptools import setup


import sys


if __name__ == "__main__":
    if sys.version_info[:2] < (3, 7):
        print('Requires Python version 3.7 or later')
        sys.exit(-1)

    setup(
        name='gambi',
        packages=find_packages(),
        version='0.01',
        description='Gambi VPL for Notebooks',
        author='Flavio Figueiredo'
    )
