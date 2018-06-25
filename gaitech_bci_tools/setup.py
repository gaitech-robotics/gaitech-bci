#!/usr/bin/env python
from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup
import glob

d = generate_distutils_setup()
d['packages'] = ['gaitech_bci_tools', 'gaitech_bci_tools.pyqt', 'gaitech_bci_tools.interface', 'gaitech_bci_tools.interface.resources']
d['package_dir'] = {'':'src'}
data_files=[]
directory = 'gaitech_bci_tools/interface/resources/'
files = glob.glob('src/'+directory+'*.png')
data_files.append(('lib/python2.7/dist-packages/'+directory, files)) # Currently hard coding it don't know the exact procedure
d['data_files'] = data_files

setup(**d)
