"""Setup script for ISA DSL package.

Note: This project now uses pyproject.toml and UV for package management.
This setup.py is kept for backward compatibility but pyproject.toml is the source of truth.
"""

from setuptools import setup, find_packages

setup(
    name='isa-dsl',
    version='0.1.1',
    description='Domain Specific Language for Instruction Set Architecture descriptions',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'textX>=3.0.0',
        'Jinja2>=3.1.0',
        'Click>=8.1.0',
    ],
    entry_points={
        'console_scripts': [
            'isa-dsl=isa_dsl.cli:cli',
        ],
    },
)

