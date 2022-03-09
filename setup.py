#
# MIT License
#
# (C) Copyright 2021-2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# setuptools-based installation module for cray-product-catalog

from os import path
import re
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

with open(path.join(here, '.version'), encoding='utf-8') as f:
    version = f.read().strip()

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    install_requires = []
    for line in f.readlines():
        if line and line[0].isalpha():
            install_requires.append(line.strip())

setup(
    name='cray-product-catalog',
    version=version,
    description='Cray Product Catalog',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Cray-HPE/cray-product-catalog',
    author='Hewlett Packard Enterprise Development LP',
    license='MIT',
    packages=find_packages(exclude=['tests', 'tests.*']),
    package_data={
        'cray_product_catalog.schema': ['schema.yaml']
    },
    python_requires='>=3, <4',
    # Top-level dependencies are parsed from requirements.txt
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'catalog_delete=cray_product_catalog.catalog_delete:main',
            'catalog_update=cray_product_catalog.catalog_update:main'
        ]
    }
)
