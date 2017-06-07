from setuptools import find_packages
from setuptools import setup
import os


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()


version = '0.7'
shortdesc = "Filesystem directory abstraction based on nodes"
longdesc = '\n\n'.join([read_file(name) for name in [
    'README.rst',
    'LICENSE.rst'
]])


setup(
    name='node.ext.directory',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    keywords='',
    author='BlueDynamics Alliance',
    author_email='dev@bluedynamics.com',
    url='http://github.com/bluedynamics/node.ext.directory',
    license='BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['node', 'node.ext'],
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'setuptools',
        'node',
        'plumber',
        'zope.interface'
    ],
    extras_require={
        'test': [
            'zope.configuration',
        ]
    },
    test_suite='node.ext.directory.tests',
    entry_points="""
    """
)
