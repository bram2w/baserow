#!/usr/bin/env python
import os

from setuptools import find_packages, setup

PROJECT_DIR = os.path.dirname(__file__)


setup(
    name="changelog",
    url="https://baserow.io",
    author="Bram Wiepjes (Baserow)",
    author_email="bram@baserow.io",
    platforms=["linux"],
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
)
