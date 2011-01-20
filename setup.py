from setuptools import setup, find_packages
import os

version = '0.1'
shortdesc = "Filesystem Directory Abstraction based on Nodes"
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()

setup(name='node.ext.directory',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Development Status :: 3 - Alpha',
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
      ], # Get strings from http://www.python.org/pypi?:action=list_classifiers
      keywords='',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url='http://github.com/bluedynamics/node.ext.directory',
      license='BSD',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['node', 'node.ext'],
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          'setuptools',
          'node',
          'plumber',
          'zope.interface',
      ],
      extras_require={
          'test': [
              'interlude',
              'zope.configuration',
          ]
      },
      entry_points="""
      [console_scripts]
      """,
      )
