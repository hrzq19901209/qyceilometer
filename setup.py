import setuptools
import os
#if os.environ.get('USER','') == 'vagrant':
del os.link
setuptools.setup(
        setup_requires=['pbr>=1.8'],
        pbr=True)