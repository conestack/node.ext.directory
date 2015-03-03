The Directory maps directly a filesystem directory. The implementation fits 
the contract for ``agx.core.interfaces.ISource``,
``agx.core.interfaces.ITarget`` and 
``node.ext.directory.interfaces.IDirectory``.

Create test env::

    >>> import os
    >>> import tempfile
    >>> tempdir = tempfile.mkdtemp()

Default file implementation::

    >>> from node.ext.directory import File
    >>> filepath = os.path.join(tempdir, "file.txt")
    >>> file = File(filepath)
    >>> file.fs_mode = 0644
    >>> file.data
    ''

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

Factories. resolved by registration length, shortest last::

    >>> import node.ext.directory
    >>> node.ext.directory.file_factories
    {...}

    >>> from node.ext.directory import Directory
    >>> dir = Directory(tempdir)
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

Create directory and read already created file by default factory::

    >>> directory = Directory(tempdir)
    >>> directory.keys()
    ['file.txt']

    >>> file = directory['file.txt']
    >>> file
    <File object 'file.txt' at ...>

Create a new directory::

    >>> rootdir = os.path.join(tempdir, "root")
    >>> directory = Directory(rootdir)
    >>> directory.fs_mode = 0750

    >>> os.path.exists(rootdir)
    False

    >>> directory()
    >>> os.path.exists(rootdir)
    True

    >>> oct(os.stat(rootdir).st_mode & 0777)
    '0750'

Change permissions and call again::

    >>> directory.fs_mode = 0700
    >>> directory()
    >>> oct(os.stat(rootdir).st_mode & 0777)
    '0700'

Add subdirectories::

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

``backup=True`` on init causes the directory to create backup files of existing
files with postfix ``.bak``::

    >>> directory = Directory(tempdir, backup=True)
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

Check wether node index is set correctly::

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

dump::

    >>> directory()
    >>> directory = Directory(tempdir, backup=True)
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

Delete file::

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

Delete Directory::

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

Clean up test Environment::

    >>> import shutil
    >>> shutil.rmtree(tempdir)
