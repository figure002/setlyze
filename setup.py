#!/usr/bin/env python

from distutils.core import setup
import glob
import os

def recursive_get_folder_patterns(pattern):
    patterns = []
    ls = glob.glob(pattern)
    for f in ls:
        if os.path.isdir(f):
            pattern = "%s/*" % f
            patterns.append(pattern)

    for pattern in patterns:
        patterns.extend(recursive_get_folder_patterns(pattern))

    return patterns

def transform_folder_patterns(folders):
    for i, f in enumerate(folders):
        # Make sure we only get files with extensions.
        if f.endswith('/*'):
            f = f.replace('/*', '/*.*')
        # Leave out the 'setlyze/' part at the beginning.
        folders[i] = f[8:]
    return folders

# Compile a list of patterns pointing to SETLyze's package data.
package_data_setlyze = recursive_get_folder_patterns('setlyze/docs/*')
package_data_setlyze = transform_folder_patterns(package_data_setlyze)
package_data_setlyze.extend(['docs/*.*'])
package_data_setlyze.extend(['images/*.*'])

setup(name='setlyze',
    version='0.1',
    description='A tool for analyzing the settlement of species.',
    long_description='A tool for analyzing the settlement of species.',
    author='Serrano Pereira',
    author_email='serrano.pereira@gmail.com',
    license='GPL3',
    platforms=['GNU/Linux','Windows'],
    scripts=['setlyze.pyw'],
    url='http://www.gimaris.com/',
    packages=['setlyze','setlyze.analysis'],
    package_data={'setlyze': package_data_setlyze},
)
