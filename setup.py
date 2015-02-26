#!/usr/bin/env python
from setuptools import setup, find_packages
from codecs import open
from os import path

from setlyze import __version__

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='setlyze',
    version=__version__,
    description='A data normalizer and transponer for files containing taxon biomass/density data for ecotopes.',
    long_description=long_description,
    url='https://github.com/figure002/setlyze',
    author='Serrano Pereira',
    author_email='serrano.pereira@gmail.com',
    license='GPL3',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Natural Language :: English",
    ],
    keywords = 'gimaris setl settlement marine species',
    packages=find_packages(exclude=['build','docs','env','tests']),
    install_requires=[
        'appdirs',
        #'PyGTK>=2.24.0,!=2.24.8,!=2.24.10',
        'pandas',
        'RPy2',
        'xlrd>=0.8',
    ],
    package_data={
        'setlyze': [
            'glade/*.glade',
            'images/*.png'
        ]
    },
    entry_points={
        'gui_scripts': [
            'setlyze = setlyze.main:main',
        ]
    }
)
