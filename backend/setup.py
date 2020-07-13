#!/usr/bin/env python
import os

from setuptools import find_packages, setup


PROJECT_DIR = os.path.dirname(__file__)
REQUIREMENTS_DIR = os.path.join(PROJECT_DIR, 'requirements')
VERSION = '0.0.2'


def get_requirements(env):
    with open(os.path.join(REQUIREMENTS_DIR, f'{env}.txt')) as fp:
        return [
            x.strip()
            for x in fp.read().split("\n")
            if not x.startswith("#")
        ]


install_requires = get_requirements('base')


setup(
    name='baserow',
    version=VERSION,
    url='https://baserow.io',
    scripts=['baserow'],
    author='Bram Wiepjes (Cloud 3)',
    author_email='bram@baserow.io',
    description='Open source online database.',
    long_description='',
    platforms=['linux'],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    install_requires=install_requires
)
