import setuptools
import os
#if os.environ.get('USER','') == 'vagrant':
del os.link
setuptools.setup(
        setup_requires=['pbr'],
        pbr=True)