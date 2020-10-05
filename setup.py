#!/usr/bin/env python

from setuptools import setup
import os
import platform

install_requires = ['numpy', 'scipy', 'scikit-image', 'matplotlib >= 2.1.2', 'tqdm', 'clickpoints >= 1.9.6',
                    "natsort"]

version = '1.0'  # adding a version file automatically
file_path = os.path.join(os.getcwd(), os.path.join("localAlignement", "_version.py"))
with open(file_path, "w") as f:
    f.write("__version__ = '%s'" % version)



setup(
    name='localAlignement',
    packages=['localAlignement'],
    version=version,
    description='traction force microscopy and FEM analysis of cell sheets',
    url='https://pytfm.readthedocs.io/',
    download_url='https://github.com/fabrylab/pyTFM.git',
    author='Andreas Bauer',
    author_email='andreas.b.bauer@fau.de',
    license='',
    install_requires=install_requires,
    keywords=['traction force microscopy', 'finite elements'],
    classifiers=[],
    include_package_data=True,
)



