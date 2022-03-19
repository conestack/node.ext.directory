node.ext.directory
==================

.. image:: https://img.shields.io/pypi/v/node.ext.directory.svg
    :target: https://pypi.python.org/pypi/node.ext.directory
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/node.ext.directory.svg
    :target: https://pypi.python.org/pypi/node.ext.directory
    :alt: Number of PyPI downloads

.. image:: https://github.com/conestack/node.ext.directory/actions/workflows/test.yaml/badge.svg
    :target: https://github.com/conestack/node.ext.directory/actions/workflows/test.yaml
    :alt: Test node.ext.directory


Overview
--------

``node.ext.directory`` is a node implementation for file system directories.

For more information about ``node`` see
`https://pypi.python.org/pypi/node <https://pypi.python.org/pypi/node>`_.


Usage
-----

Create new file:

.. code-block:: python

    from node.ext.directory import File

    file_path = 'file.txt'
    f = File(name=file_path)

    # set contents via data attribute
    f.data = 'data\n'

    # set contents via lines attribute
    f.lines = ['data']

    # set permissions
    f.fs_mode = 0o644

    # persist
    f()

Read existing file:

.. code-block:: python

    file_path = 'file.txt'
    f = File(name=file_path)

    assert(f.data == 'data\n')
    assert(f.lines == ['data'])
    assert(f.fs_mode == 0o644)

Files with binary data:

.. code-block:: python

    from node.ext.directory import MODE_BINARY

    file_path = 'file.txt'
    f = File(name=file_path)
    f.mode = MODE_BINARY

    f.data = b'\x00\x00'

    assert(f.data == b'\x00\x00')

    # lines property won't work if file in binary mode
    f.lines  # raises RuntimeError

Create directory:

.. code-block:: python

    from node.ext.directory import Directory

    dir_path = '.'
    d = Directory(name=dir_path)

    # add subdirectories and files
    d['sub'] = Directory()
    d['file.txt'] = File()

    # set permissions for directory
    d['sub'].fs_mode = 0o755

    # persist
    d()

Read existing directory:

.. code-block:: python

    dir_path = '.'
    d = Directory(name=dir_path)

.. code-block:: pycon

    >>> d.printtree()
    <class 'node.ext.directory.directory.Directory'>: .
      <class 'node.ext.directory.directory.File'>: file.txt
      <class 'node.ext.directory.directory.Directory'>: sub

Define file factories:

.. code-block:: python

    from node.ext import directory

    class PyFile(File):
        pass

    # set global factories
    directory.file_factories['.py'] = PyFile

    # set local factories
    d = Directory(name='.', factories={'.py': PyFile})

when reading .py files, PyFile is used to instanciate children:

.. code-block:: pycon

    >>> with open('foo.py', 'w') as f:
    ...     f.write('#')

    >>> d = Directory(name='.', factories={'.py': PyFile})
    >>> d.printtree()
    <class 'node.ext.directory.directory.Directory'>: .
      <class '...PyFile'>: foo.py


Python Versions
===============

- Python 2.7, 3.7+
- May work with other versions (untested)


Contributors
============

- Robert Niederreiter (Author)
