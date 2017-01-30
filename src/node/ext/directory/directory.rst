==================
node.ext.directory
==================

Test related imports:

.. code-block:: pycon

    >>> from node.behaviors import Adopt
    >>> from node.behaviors import DefaultInit
    >>> from node.behaviors import DictStorage
    >>> from node.behaviors import Nodify
    >>> from node.behaviors import Reference
    >>> from node.ext.directory import Directory
    >>> from node.ext.directory import File
    >>> from node.ext.directory import MODE_BINARY
    >>> from plumber import plumbing
    >>> import node.ext.directory
    >>> import os
    >>> import shutil
    >>> import tempfile

Create test env:

.. code-block:: pycon

    >>> tempdir = tempfile.mkdtemp()

Default file implementation:

.. code-block:: pycon

    >>> filepath = os.path.join(tempdir, "file.txt")
    >>> file = File(filepath)
    >>> file.fs_mode = 0644
    >>> file.direct_sync = True
    >>> file.data
    ''

    >>> file.lines
    []

    >>> os.path.exists(filepath)
    False

    >>> file()

    >>> os.path.exists(filepath)
    True

    >>> oct(os.stat(filepath).st_mode & 0777)
    '0644'

    >>> file.fs_mode = 0600
    >>> file()
    >>> oct(os.stat(filepath).st_mode & 0777)
    '0600'

    >>> with open(filepath) as f:
    ...     out = f.read()
    >>> out
    ''

    >>> file.data = "abc\ndef"
    >>> file()
    >>> with open(filepath) as f:
    ...     out = f.readlines()
    >>> out
    ['abc\n', 'def']

    >>> file = File(filepath)
    >>> file.data
    'abc\ndef'

    >>> file.lines
    ['abc', 'def']

    >>> file.lines = ['a', 'b', 'c']
    >>> file()
    >>> with open(filepath) as f:
    ...     out = f.read()
    >>> out
    'a\nb\nc'

Binary File:

.. code-block:: pycon

    >>> bin_filepath = os.path.join(tempdir, "file.bin")

    >>> class BinaryFile(File):
    ...     mode = MODE_BINARY

    >>> bin_file = BinaryFile(bin_filepath)
    >>> bin_file.data

    >>> bin_file.lines
    Traceback (most recent call last):
      ...
    RuntimeError: Cannot read lines from binary file.

    >>> bin_file.lines = []
    Traceback (most recent call last):
      ...
    RuntimeError: Cannot write lines to binary file.

File with unicode name:

.. code-block:: pycon

    >>> directory = Directory(name=tempdir)
    >>> directory[u'ä'] = File()

    >>> directory()

    >>> sorted(os.listdir(tempdir))
    ['file.txt', '\xc3\x83\xc2\xa4']

    >>> directory = Directory(name=tempdir)
    >>> directory[u'ä']
    <File object 'Ã¤' at ...>

    >>> os.remove(os.path.join(tempdir, u'ä'))

Factories. resolved by registration length, shortest last:

.. code-block:: pycon

    >>> node.ext.directory.file_factories
    {...}

    >>> dir = Directory(name=tempdir)
    >>> dir.factories
    {}

    >>> dir._factory_for_ending('foo')

    >>> def dummy_txt_factory(): pass
    >>> node.ext.directory.file_factories['.txt'] = dummy_txt_factory
    >>> def dummy_foo_factory(): pass
    >>> node.ext.directory.file_factories['foo.txt'] = dummy_foo_factory

    >>> dir._factory_for_ending('bar.txt')
    <function dummy_txt_factory at ...>

    >>> dir._factory_for_ending('foo.txt')
    <function dummy_foo_factory at ...>

    >>> def dummy_local_txt_factory(): pass
    >>> dir.factories['.txt'] = dummy_local_txt_factory

    >>> dir._factory_for_ending('bar.txt')
    <function dummy_local_txt_factory at ...>

    >>> dir._factory_for_ending('foo.txt')
    <function dummy_foo_factory at ...>

    >>> def dummy_local_foo_factory(): pass
    >>> dir.factories['foo.txt'] = dummy_local_foo_factory

    >>> dir._factory_for_ending('foo.txt')
    <function dummy_local_foo_factory at ...>

    >>> del node.ext.directory.file_factories['.txt']
    >>> del node.ext.directory.file_factories['foo.txt']
    >>> del dir.factories['.txt']
    >>> del dir.factories['foo.txt']

Factories can be given at directory init time:

.. code-block:: pycon

    >>> directory = Directory(name=tempdir, factories={
    ...     '.txt': dummy_txt_factory
    ... })

    >>> directory.factories
    {'.txt': <function dummy_txt_factory at ...>}

Try to read file by broken factory, falls back to ``File``:

.. code-block:: pycon

    >>> class SaneFile(File):
    ...     pass

    >>> def sane_factory():
    ...     return SaneFile()

    >>> directory = Directory(name=tempdir, factories={
    ...     '.txt': sane_factory
    ... })

    >>> directory['file.txt']
    <SaneFile object 'file.txt' at ...>

    >>> def broken_factory(param):
    ...     return SaneFile()

    >>> directory = Directory(name=tempdir, factories={
    ...     '.txt': broken_factory
    ... })

    >>> directory['file.txt']
    <File object 'file.txt' at ...>

Create directory and read already created file by default factory:

.. code-block:: pycon

    >>> directory = Directory(name=tempdir)
    >>> directory.keys()
    ['file.txt']

    >>> file = directory['file.txt']
    >>> file
    <File object 'file.txt' at ...>

Create a new directory which cannot be persisted:

.. code-block:: pycon

    >>> invalid_dir = os.path.join(tempdir, 'invalid_dir')

    >>> with open(invalid_dir, 'w') as file:
    ...     file.write('')

    >>> os.path.exists(invalid_dir)
    True

    >>> os.path.isdir(invalid_dir)
    False

    >>> directory = Directory(name=invalid_dir)
    >>> directory()
    Traceback (most recent call last):
      ...
    KeyError: 'Attempt to create a directory with name which already exists 
    as file'

    >>> os.remove(invalid_dir)

Create a new directory:

.. code-block:: pycon

    >>> rootdir = os.path.join(tempdir, "root")
    >>> directory = Directory(name=rootdir)
    >>> directory.fs_mode = 0750

    >>> os.path.exists(rootdir)
    False

    >>> directory()
    >>> os.path.exists(rootdir)
    True

    >>> oct(os.stat(rootdir).st_mode & 0777)
    '0750'

Change permissions and call again:

.. code-block:: pycon

    >>> directory.fs_mode = 0700
    >>> directory()
    >>> oct(os.stat(rootdir).st_mode & 0777)
    '0700'

Add subdirectories:

.. code-block:: pycon

    >>> directory[''] = Directory()
    Traceback (most recent call last):
      ...
    KeyError: 'Empty key not allowed in directories'

    >>> directory['subdir1'] = Directory()
    >>> directory['subdir1'].fs_mode = 0770
    >>> directory['subdir2'] = Directory()
    >>> directory['subdir2'].fs_mode = 0755
    >>> directory.printtree()
    <class 'node.ext.directory.directory.Directory'>: /.../root
      <class 'node.ext.directory.directory.Directory'>: subdir2
      <class 'node.ext.directory.directory.Directory'>: subdir1

    >>> directory.keys()
    ['subdir2', 'subdir1']

    >>> os.listdir(os.path.join(*directory.path))
    []

    >>> directory()
    >>> sorted(os.listdir(os.path.join(*directory.path)))
    ['subdir1', 'subdir2']

    >>> subdir1_path = os.path.join(
    ...     *directory.path + [directory['subdir1'].name])
    >>> oct(os.stat(subdir1_path).st_mode & 0777)
    '0770'

    >>> subdir2_path = os.path.join(
    ...     *directory.path + [directory['subdir2'].name])
    >>> oct(os.stat(subdir2_path).st_mode & 0777)
    '0755'

Add invalid child node:

.. code-block:: pycon

    >>> @plumbing(
    ...     Adopt,
    ...     DefaultInit,
    ...     Reference,
    ...     Nodify,
    ...     DictStorage)
    ... class NoFile(object):
    ...     pass

    >>> directory['unknown'] = NoFile()
    Traceback (most recent call last):
      ...
    ValueError: Unknown child node.

Path lookup on ``File`` implementations without ``fs_path`` property falls back
to ``path`` property:

.. code-block:: pycon

    >>> class FileWithoutFSPath(File):
    ...     @property
    ...     def fs_path(self):
    ...         raise AttributeError

    >>> no_fs_path_file = directory['no_fs_path_file'] = FileWithoutFSPath()
    >>> hasattr(no_fs_path_file, 'fs_path')
    False

    >>> directory()

    >>> no_fs_path = os.path.join(*directory.fs_path + ['no_fs_path_file'])
    >>> os.path.exists(no_fs_path)
    True

    >>> os.remove(no_fs_path)

Ignore children in directories:

.. code-block:: pycon

    >>> class DirectoryWithIgnores(Directory):
    ...     ignores = ['file.txt']

    >>> sorted(os.listdir(tempdir))
    ['file.txt', 'root']

    >>> directory = DirectoryWithIgnores(name=tempdir)
    >>> directory.keys()
    ['root']

``backup=True`` on init causes the directory to create backup files of existing
files with postfix ``.bak``:

.. code-block:: pycon

    >>> directory = Directory(name=tempdir, backup=True)
    >>> directory.keys()
    ['file.txt', 'root']

    >>> directory['file.txt']
    <File object 'file.txt' at ...>

    >>> directory['root']
    <Directory object 'root' at ...>

    >>> directory['root'].keys()
    ['subdir2', 'subdir1']

    >>> directory['root'].backup
    True

    >>> directory['root']['profile'] = Directory()
    >>> directory['root']['profile']
    <Directory object 'profile' at ...>

    >>> directory['root'].keys()
    ['profile', 'subdir2', 'subdir1']
  
    >>> directory['root']['profile'].path
    ['...root', 'profile']

    >>> directory['root']['profile']['types'] = Directory()
    >>> directory['root']['profile']['types'] 
    <Directory object 'types' at ...>

    >>> directory['root']['__init__.py'] = File()
    >>> directory['root']['__init__.py']
    <File object '__init__.py' at ...>

Check wether node index is set correctly:

.. code-block:: pycon

    >>> directory.printtree()
    <class 'node.ext.directory.directory.Directory'>: /...
      <class 'node.ext.directory.directory.File'>: file.txt
      <class 'node.ext.directory.directory.Directory'>: root
        <class 'node.ext.directory.directory.Directory'>: profile
          <class 'node.ext.directory.directory.Directory'>: types
        <class 'node.ext.directory.directory.Directory'>: subdir2
        <class 'node.ext.directory.directory.File'>: __init__.py
        <class 'node.ext.directory.directory.Directory'>: subdir1
  
    >>> len(directory._index)
    8

dump:

.. code-block:: pycon

    >>> directory()
    >>> directory = Directory(name=tempdir, backup=True)
    >>> directory.factories['.py'] = File
    >>> directory.keys()
    ['file.txt', 'root']

    >>> directory.printtree()
    <class 'node.ext.directory.directory.Directory'>: /...
      <class 'node.ext.directory.directory.File'>: file.txt
      <class 'node.ext.directory.directory.Directory'>: root
        <class 'node.ext.directory.directory.Directory'>: profile
          <class 'node.ext.directory.directory.Directory'>: types
        <class 'node.ext.directory.directory.Directory'>: subdir2
        <class 'node.ext.directory.directory.File'>: __init__.py
        <class 'node.ext.directory.directory.Directory'>: subdir1

    >>> sorted(os.listdir(os.path.join(*directory.path)))
    ['.file.txt.bak', 'file.txt', 'root']

    >>> sorted(os.listdir(os.path.join(*directory['root'].path)))
    ['.__init__.py.bak', '__init__.py', 'profile', 'subdir1', 'subdir2']

Delete file:

.. code-block:: pycon

    >>> del directory['file.txt']
    >>> len(directory._index)
    7

    >>> directory.keys()
    ['root']

    >>> directory._deleted
    ['file.txt']

    >>> sorted(os.listdir(tempdir))
    ['.file.txt.bak', 'file.txt', 'root']

    >>> directory()
    >>> os.listdir(tempdir)
    ['root']

    >>> directory._deleted
    []

Delete Directory:

.. code-block:: pycon

    >>> del directory['root']['profile']
    >>> len(directory._index)
    5

    >>> sorted(directory['root'].keys())
    ['__init__.py', 'subdir1', 'subdir2']

    >>> sorted(os.listdir(rootdir))
    ['.__init__.py.bak', '__init__.py', 'profile', 'subdir1', 'subdir2']

    >>> directory()
    >>> sorted(os.listdir(rootdir))
    ['.__init__.py.bak', '__init__.py', 'subdir1', 'subdir2']

Clean up test Environment:

.. code-block:: pycon

    >>> shutil.rmtree(tempdir)
