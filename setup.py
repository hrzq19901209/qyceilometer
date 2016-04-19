import setuptools
import os
#if os.environ.get('USER','') == 'vagrant':
del os.link #在虚拟机上测试要删除os.link 不然会报错
setuptools.setup(
        setup_requires=['pbr'],
        pbr=True)