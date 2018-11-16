"""News Reader setup"""
from setuptools import setup, find_packages

setup(
    name="newsreader",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'nr=nr.main:main'],
    },
    data_files=[
        ('man/man1', ['doc/man/nr.1']),
        ('man/man5', ['doc/man/nr-config.5']),
    ],
    install_requires=[
        'urwid',
        'requests',
        'requests-cache',
        'beautifulsoup4',
    ]
)
