#!/usr/bin/env python
import os

from setuptools import find_packages, setup

PROJECT_DIR = os.path.dirname(__file__)
REQUIREMENTS_DIR = os.path.join(PROJECT_DIR, 'requirements')


with open(os.path.join(REQUIREMENTS_DIR, 'base.txt'), 'r') as r:
    install_requires = r.read()


with open(os.path.join(REQUIREMENTS_DIR, 'dev.txt'), 'r') as r:
    develop_requires = r.read()


setup(
    name='baserow',
    version='1.0.0',
    url='',
    author='Bram Wiepjes (Cloud 3)',
    author_email='bram@baserow.io',
    description='',
    long_description='',
    platforms=['linux'],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'dev':  develop_requires,
    },
)
