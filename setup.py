#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
#import re

version = '1.0'
#with open('pycontrol/__init__.py', 'r') as fd:
#    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
#                        fd.read(), re.MULTILINE).group(1)

#if not version:
#    raise RuntimeError('Cannot find version information')

setup(
    name='pycontrol',
    version=version,
    description="""pyControl is a behavioral experiments control system written in Python 3""",
    author='Thomas Akam',
    author_email='cajomferro@gmail.com',
    license='Copyright (c) [2016] [Champalimaud Foundation] The MIT License (MIT)',
    url='https://bitbucket.org/fchampalimaud/pycontrol-framework-api',

    include_package_data=True,
    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'examples', 'deploy', 'reports']),

    install_requires=[
        "pyserial >= 3.1.1",
    #    "logging-bootstrap >= 0.1"
    ],

    #entry_points={
    #    'console_scripts': [
    #        'pycontrol-cli=pycontrol.__main__:start',
    #    ],
    #}
)