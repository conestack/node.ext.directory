==================
node.ext.directory
==================

Filesystem directory abstraction based on
`node <https://pypi.python.org/pypi/node>`_.


Usage
=====

Create new file
---------------

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


Read existing file
------------------

.. code-block:: python

    file_path = 'file.txt'
    f = File(name=file_path)

    assert(f.data == 'data\n')
    assert(f.lines == ['data'])
    assert(f.fs_mode == 0o644)


Files with binary data
----------------------

.. code-block:: python

    from node.ext.directory import MODE_BINARY

    file_path = 'file.txt'
    f = File(name=file_path)
    f.mode = MODE_BINARY

    f.data = b'\x00\x00'

    assert(f.data == b'\x00\x00')

    # lines property won't work if file in binary mode
    f.lines  # raises RuntimeError


Create directory
----------------

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


Read existing directory
-----------------------

.. code-block:: python

    dir_path = '.'
    d = Directory(name=dir_path)

.. code-block:: pycon

    >>> d.printtree()
    <class 'node.ext.directory.directory.Directory'>: .
      <class 'node.ext.directory.directory.File'>: file.txt
      <class 'node.ext.directory.directory.Directory'>: sub


Define file factories
---------------------

.. code-block:: python

    from node.ext import directory

    class PyFile(File):
        pass

    # set global factories
    directory.file_factories['.py'] = PyFile

    # set local factories
    d = Directory(name='.', factories={'.py': PyFile})

.. code-block:: pycon

    # when reading .py files, PyFile is used to instanciate children
    >>> with open('foo.py', 'w') as f:
    ...     f.write('#')

    >>> d = Directory(name='.', factories={'.py': PyFile})
    >>> d.printtree()
    <class 'node.ext.directory.directory.Directory'>: .
      <class '...PyFile'>: foo.py


TestCoverage
============

.. image:: https://travis-ci.org/bluedynamics/node.ext.directory.svg?branch=master
    :target: https://travis-ci.org/bluedynamics/node.ext.directory

Summary of the test coverage report::

    Name                                                    Stmts   Miss  Cover
    ---------------------------------------------------------------------------
    src/node/ext/directory/__init__.py                          7      0   100%
    src/node/ext/directory/directory.py                       221      0   100%
    src/node/ext/directory/events.py                            5      0   100%
    src/node/ext/directory/interfaces.py                       23      0   100%
    src/node/ext/directory/tests.py                           335      0   100%
    ---------------------------------------------------------------------------
    TOTAL                                                     591      0   100%


Python Versions
===============

- Python 2.7, 3.3+, pypy

- May work with other versions (untested)


Contributors
============

- Robert Niederreiter (Author)


TODO
====

- Documentation.

- Remove lifecycle event notification on ``__setitem__`` in directory. Use
  ``node.behaviors.Lifecycle`` instead

- Suppress lifecycle events in ``_create_child_by_factory``.

- Remove ``Reference`` plumbing behavior from default ``File`` and
  ``Directory`` implementations.

- Rename ``DirectoryStorage.factories`` to ``DirectoryStorage.file_factories``.

- Use regular expressions for child factories if desired.

- Introduce flag on ``DirectoryStorage`` to turn off RAM caching of children.

- Introduce strict mode which prevents fallback ``File`` creation if file
  factory raises ``TypeError``.


Changes
=======

0.7
---

- Python 3 support.
  [rnix, 2017-06-06]

- ``fs_mode`` is read from filesystem if file or directory exists and
  fs_mode not set explicitely.
  [rnix, 2017-06-06]

- Remove ``backup`` option from ``IDirectory`` interface. It never really
  worked properly and conceptually ``IDirectory`` is the wrong place for
  handling backups of files.
  [rnix, 2017-06-04]


0.6
---

- Introduce ``node.ext.directory.interfaces.IFile.direct_sync`` setting.
  [rnix, 2017-01-30]

- Complete ``node.ext.directory.interfaces.IFile`` and
  ``node.ext.directory.interfaces.IDirectory`` to reflect implemented features.
  [rnix, 2017-01-30]

- Move ``node.ext.directory.directory.MODE_TEXT`` and
  ``node.ext.directory.directory.MODE_BINARY`` to
  ``node.ext.directory.interfaces``.
  [rnix, 2017-01-30]


0.5.4
-----

- Check whether directory to be peristed already exists by name as file in
  ``node.ext.directory.FileStorage.__call__``.
  [rnix, 2015-10-05]

- Implement fallback to ``path`` in
  ``node.ext.directory.FileStorage.__call__`` if ``fs_path`` not exists.
  [rnix, 2015-10-05]

- Implement fallback to ``path`` in
  ``node.ext.directory.FileStorage._get_data`` if ``fs_path`` not exists.
  [rnix, 2015-10-05]

- Set initial mode with ``self.mode`` property setter instead of internal
  ``self._mode`` in ``node.ext.directory.FileStorage._get_mode``.
  [rnix, 2015-10-05]


0.5.3
-----

- Remove deleted keys from internal reference after ``__call__`` in order
  to return the correct result when adding a file or directory with the same
  key again.
  [rnix, 2015-07-20]


0.5.2
-----

- Use try/except instead of iteration to check whether directory child already
  in memory.
  [rnix, 2015-05-12]


0.5.1
-----

- Always use ``os.chmod`` for setting directory permissions, not only if
  already exists.
  [rnix, 2015-03-03]


0.5
---

- Introduce ``fs_mode`` on directories and files.
  [rnix, 2015-03-03]


0.4
---

- Return empty list in ``File.lines`` if no data.
  [rnix, 2015-02-18]

- Consider filesystem encoding. Defaults to UTF-8.
  [rnix, 2015-02-18]

- Tree locking on modification.
  [rnix, 2014-09-02]

- Prevent empty keys in ``__setitem__``.
  [rnix, 2014-09-02]

- Use ``plumbing`` decorator.
  [rnix, 2014-08-25]


0.3
---

- introduce ``default_file_factory`` on directories for controlling default
  file child creation.
  [rnix, 2013-12-09]

- move file logic in ``FileStorage`` behavior.
  [rnix, 2013-08-06]

- make ``file_factories`` a class property on directory storage.
  [rnix, 2013-08-06]

- make ``ignores`` a class property on directory storage.
  [rnix, 2013-08-06]

- Cleanup interfaces.
  [rnix, 2013-08-06]


0.2
---

- Almost complete rewrite. Fits now paradigms of node based API's.
  [rnix, 2012-01-30]


0.1
---

- initial
