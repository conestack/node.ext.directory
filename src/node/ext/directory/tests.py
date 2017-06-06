# -*- coding: utf-8 -*-
from node.behaviors import Adopt
from node.behaviors import DefaultInit
from node.behaviors import DictStorage
from node.behaviors import Nodify
from node.behaviors import Reference
from node.compat import IS_PY2
from node.ext.directory import Directory
from node.ext.directory import File
from node.ext.directory import MODE_BINARY
from node.ext.directory import MODE_TEXT
from node.ext.directory import directory
from node.ext.directory.events import IFileAddedEvent
from node.ext.directory.interfaces import IDirectory
from node.ext.directory.interfaces import IFile
from node.tests import NodeTestCase
from node.tests import patch
from plumber import plumbing
from zope import component
import logging
import node.ext.directory
import os
import shutil
import tempfile
import unittest


###############################################################################
# Mock objects
###############################################################################

class Handler(object):
    handled = []

    def __call__(self, obj, event):
        self.handled.append(event)

    def clear(self):
        self.handled = []


class DummyLogger(object):
    log_levels = {
        10: 'DEBUG',
        20: 'INFO',
        30: 'WARNING',
        40: 'ERROR',
    }

    def __init__(self):
        self.messages = list()

    def clear(self):
        self.messages = list()

    def log(self, level, message):
        self.messages.append(
            '{0}: {1}'.format(self.log_levels[level], message).strip()
        )

    def warning(self, message):
        self.log(logging.WARNING, message)

    def error(self, message):
        self.log(logging.ERROR, message)


dummy_logger = DummyLogger()


###############################################################################
# Tests
###############################################################################

class TestDirectory(NodeTestCase):

    def setUp(self):
        super(TestDirectory, self).setUp()
        self.tempdir = tempfile.mkdtemp()
        handler = self.handler = Handler()
        component.provideHandler(handler, [IFile, IFileAddedEvent])
        component.provideHandler(handler, [IDirectory, IFileAddedEvent])

    def tearDown(self):
        super(TestDirectory, self).tearDown()
        dummy_logger.clear()
        shutil.rmtree(self.tempdir)

    def test_file_persistance(self):
        filepath = os.path.join(self.tempdir, 'file.txt')
        file = File(name=filepath)
        file.direct_sync = True
        self.assertFalse(os.path.exists(filepath))
        file()
        self.assertFalse(os.path.isdir(filepath))
        self.assertTrue(os.path.exists(filepath))
        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, '')

    def test_file_mode_text(self):
        filepath = os.path.join(self.tempdir, 'file.txt')
        file = File(name=filepath)
        file.direct_sync = True

        self.assertEqual(file.mode, MODE_TEXT)
        self.assertEqual(file.data, '')
        self.assertEqual(file.lines, [])

        file.data = 'abc\ndef'
        file()
        with open(filepath) as f:
            out = f.readlines()
        self.assertEqual(out, ['abc\n', 'def'])

        file = File(name=filepath)
        self.assertEqual(file.data, 'abc\ndef')
        self.assertEqual(file.lines, ['abc', 'def'])

        file.lines = ['a', 'b', 'c']
        file()
        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, 'a\nb\nc')

    def test_file_mode_binary(self):
        filepath = os.path.join(self.tempdir, 'file.bin')

        class BinaryFile(File):
            mode = MODE_BINARY

        file = BinaryFile(name=filepath)
        self.assertEqual(file.data, None)

        err = self.expect_error(RuntimeError, lambda: file.lines)
        self.assertEqual(str(err), 'Cannot read lines from binary file.')

        def set_lines_fails():
            file.lines = []
        err = self.expect_error(RuntimeError, set_lines_fails)
        self.assertEqual(str(err), 'Cannot write lines to binary file.')

        file.data = b'\x00\x00'
        file()
        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, '\x00\x00')

    def test_file_permissions(self):
        filepath = os.path.join(self.tempdir, 'file.txt')
        file = File(name=filepath)
        self.assertEqual(file.fs_mode, None)

        file.fs_mode = 0o644
        file.direct_sync = True

        file()
        self.assertTrue(os.path.exists(filepath))
        self.assertEqual(os.stat(filepath).st_mode & 0o777, 0o644)

        file.fs_mode = 0o600
        file()
        self.assertEqual(os.stat(filepath).st_mode & 0o777, 0o600)

        file = File(name=filepath)
        self.assertEqual(file.fs_mode, 0o600)

    def test_file_with_unicode_name(self):
        directory = Directory(name=self.tempdir)
        directory[u'ä'] = File()
        directory()

        expected = os.listdir(self.tempdir)[0]
        expected = expected.decode('utf-8') if IS_PY2 else expected
        self.assertEqual(expected, u'ä')

        directory = Directory(name=self.tempdir)
        expected = '\xc3\xa4' if IS_PY2 else u'ä'
        self.assertEqual(directory[u'ä'].name, expected)

    @patch(directory, 'logger', dummy_logger)
    def test_file_factories(self):
        # Factories. resolved by registration length, shortest last
        self.check_output("""\
        {...}
        """, str(node.ext.directory.file_factories))

        dir = Directory(name=self.tempdir)
        self.assertEqual(dir.factories, {})
        self.assertEqual(dir._factory_for_ending('foo'), None)

        def dummy_txt_factory():
            pass                                              # pragma no cover

        def dummy_foo_factory():
            pass                                              # pragma no cover

        node.ext.directory.file_factories['.txt'] = dummy_txt_factory
        node.ext.directory.file_factories['foo.txt'] = dummy_foo_factory
        self.assertEqual(dir._factory_for_ending('bar.txt'), dummy_txt_factory)
        self.assertEqual(dir._factory_for_ending('foo.txt'), dummy_foo_factory)

        def dummy_local_txt_factory():
            pass                                              # pragma no cover

        dir.factories['.txt'] = dummy_local_txt_factory
        self.assertEqual(
            dir._factory_for_ending('bar.txt'),
            dummy_local_txt_factory
        )
        self.assertEqual(
            dir._factory_for_ending('foo.txt'),
            dummy_foo_factory
        )

        def dummy_local_foo_factory():
            pass                                              # pragma no cover

        dir.factories['foo.txt'] = dummy_local_foo_factory
        self.assertEqual(
            dir._factory_for_ending('foo.txt'),
            dummy_local_foo_factory
        )

        del node.ext.directory.file_factories['.txt']
        del node.ext.directory.file_factories['foo.txt']
        del dir.factories['.txt']  # needed?
        del dir.factories['foo.txt']  # needed?

        # Factories can be given at directory init time
        directory = Directory(name=self.tempdir, factories={
            '.txt': dummy_txt_factory
        })
        self.assertEqual(directory.factories, {'.txt': dummy_txt_factory})

        # Try to read file by broken factory, falls back to ``File``
        class SaneFile(File):
            pass

        def sane_factory():
            return SaneFile()

        filepath = os.path.join(self.tempdir, 'file.txt')
        with open(filepath, 'w') as f:
            f.write('')

        directory = Directory(name=self.tempdir, factories={
            '.txt': sane_factory
        })
        expected = '<SaneFile object \'file.txt\' at '
        self.assertTrue(str(directory['file.txt']).startswith(expected))

        def broken_factory(param):
            return SaneFile()                                 # pragma no cover

        directory = Directory(name=self.tempdir, factories={
            '.txt': broken_factory
        })

        expected = '<File object \'file.txt\' at '
        self.assertTrue(str(directory['file.txt']).startswith(expected))

        expected = (
            'ERROR: File creation by factory failed. Fall back to ``File``. '
            'Reason: {}'.format((
                'broken_factory() takes exactly 1 argument (0 given)'
            ) if IS_PY2 else (
                'broken_factory() missing 1 required positional argument: '
                '\'param\''
            ))
        )
        self.assertEqual(dummy_logger.messages, [expected])

        # Create directory and read already created file by default factory
        directory = Directory(name=self.tempdir)
        self.assertEqual(list(directory.keys()), ['file.txt'])

        expected = '<File object \'file.txt\' at '
        self.assertTrue(str(directory['file.txt']).startswith(expected))

    def test_file_fs_path_fallback(self):
        # Path lookup on ``File`` implementations without ``fs_path`` property
        # falls back to ``path`` property
        class FileWithoutFSPath(File):
            @property
            def fs_path(self):
                raise AttributeError

        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        no_fs_path_file = directory['no_fs_path_file'] = FileWithoutFSPath()
        self.assertFalse(hasattr(no_fs_path_file, 'fs_path'))

        directory()

        no_fs_path = os.path.join(*directory.fs_path + ['no_fs_path_file'])
        self.assertTrue(os.path.exists(no_fs_path))

    def test_directory_already_exists_as_file(self):
        # Create a new directory which cannot be persisted
        invalid_dir = os.path.join(self.tempdir, 'invalid_dir')
        with open(invalid_dir, 'w') as f:
            f.write('')

        self.assertTrue(os.path.exists(invalid_dir))
        self.assertFalse(os.path.isdir(invalid_dir))

        directory = Directory(name=invalid_dir)
        err = self.expect_error(KeyError, directory)
        expected = '\'Attempt to create a directory with name which already ' \
                   'exists as file\''
        self.assertEqual(str(err), expected)

    def test_directory_persistence(self):
        dirpath = os.path.join(self.tempdir, 'root')
        directory = Directory(name=dirpath)

        self.assertFalse(os.path.exists(dirpath))

        directory()
        self.assertTrue(os.path.exists(dirpath))
        self.assertTrue(os.path.isdir(dirpath))

    def test_directory_permissions(self):
        dirpath = os.path.join(self.tempdir, 'root')
        directory = Directory(name=dirpath)
        self.assertEqual(directory.fs_mode, None)

        directory.fs_mode = 0o750
        directory()
        self.assertEqual(os.stat(dirpath).st_mode & 0o777, 0o750)

        directory.fs_mode = 0o700
        directory()
        self.assertEqual(os.stat(dirpath).st_mode & 0o777, 0o700)

        directory = Directory(name=dirpath)
        self.assertEqual(directory.fs_mode, 0o700)

    def test_add_sub_directories(self):
        # Create a directory and add sub directories
        directory = Directory(name=os.path.join(self.tempdir, 'root'))

        def add_directory_fails():
            directory[''] = Directory()
        err = self.expect_error(KeyError, add_directory_fails)
        self.assertEqual(str(err), '\'Empty key not allowed in directories\'')

        directory['subdir1'] = Directory()
        directory['subdir2'] = Directory()

        self.check_output("""\
        <class 'node.ext.directory.directory.Directory'>: /.../root
          <class 'node.ext.directory.directory.Directory'>: subdir1
          <class 'node.ext.directory.directory.Directory'>: subdir2
        """, directory.treerepr())

        fs_path = os.path.join(*directory.path)
        self.assertEqual(sorted(directory.keys()), ['subdir1', 'subdir2'])
        self.assertFalse(os.path.exists(fs_path))

        directory()
        self.assertEqual(
            sorted(os.listdir(fs_path)),
            ['subdir1', 'subdir2']
        )

        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        self.check_output("""\
        <class 'node.ext.directory.directory.Directory'>: /.../root
          <class 'node.ext.directory.directory.Directory'>: subdir1
          <class 'node.ext.directory.directory.Directory'>: subdir2
        """, directory.treerepr())

    def test_delete_from_directory(self):
        directory = Directory(name=os.path.join(self.tempdir))
        directory['file.txt'] = File()
        directory['subdir'] = Directory()

        self.assertEqual(sorted(os.listdir(self.tempdir)), [])

        directory()
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['file.txt', 'subdir']
        )

        del directory['file.txt']
        self.assertEqual(directory._deleted, ['file.txt'])
        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['file.txt', 'subdir']
        )
        directory()
        self.assertEqual(directory._deleted, [])
        self.assertEqual(sorted(os.listdir(self.tempdir)), ['subdir'])

        del directory['subdir']
        self.assertEqual(directory._deleted, ['subdir'])
        self.assertEqual(sorted(os.listdir(self.tempdir)), ['subdir'])
        directory()
        self.assertEqual(directory._deleted, [])
        self.assertEqual(sorted(os.listdir(self.tempdir)), [])

    def test_directory___getitem__(self):
        directory = Directory(name=os.path.join(self.tempdir))
        directory['file.txt'] = File()
        directory['subdir'] = Directory()
        directory()

        directory = Directory(name=os.path.join(self.tempdir))

        expected = '<File object \'file.txt\' at '
        self.assertTrue(str(directory['file.txt']).startswith(expected))

        expected = '<Directory object \'subdir\' at '
        self.assertTrue(str(directory['subdir']).startswith(expected))

        def __getitem__fails():
            directory['inexistent']
        err = self.expect_error(KeyError, __getitem__fails)
        self.assertEqual(str(err), '\'inexistent\'')

    def test_sub_directory_permissions(self):
        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        directory.fs_mode = 0o777

        subdir1 = directory['subdir1'] = Directory()
        subdir1.fs_mode = 0o770

        subdir2 = directory['subdir2'] = Directory()
        subdir2.fs_mode = 0o755

        directory()

        dir_path = os.path.join(*directory.fs_path)
        self.assertEqual(os.stat(dir_path).st_mode & 0o777, 0o777)

        dir_path = os.path.join(*subdir1.fs_path)
        self.assertEqual(os.stat(dir_path).st_mode & 0o777, 0o770)

        dir_path = os.path.join(*subdir2.fs_path)
        self.assertEqual(os.stat(dir_path).st_mode & 0o777, 0o755)

        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        self.assertEqual(directory.fs_mode, 0o777)
        self.assertEqual(directory['subdir1'].fs_mode, 0o770)
        self.assertEqual(directory['subdir2'].fs_mode, 0o755)

    def test_add_invalid_child(self):
        # Add invalid child node
        @plumbing(
            Adopt,
            DefaultInit,
            Reference,
            Nodify,
            DictStorage)
        class NoFile(object):
            pass

        directory = Directory(name=os.path.join(self.tempdir, 'root'))

        def add_child_fails():
            directory['unknown'] = NoFile()
        err = self.expect_error(ValueError, add_child_fails)
        self.assertEqual(str(err), 'Unknown child node.')

    def test_ignore_children(self):
        # Ignore children in directories
        with open(os.path.join(self.tempdir, 'file1.txt'), 'w') as f:
            f.write('')
        with open(os.path.join(self.tempdir, 'file2.txt'), 'w') as f:
            f.write('')

        class DirectoryWithIgnores(Directory):
            ignores = ['file1.txt']

        self.assertEqual(
            sorted(os.listdir(self.tempdir)),
            ['file1.txt', 'file2.txt']
        )

        directory = DirectoryWithIgnores(name=self.tempdir)
        self.assertEqual(list(directory.keys()), ['file2.txt'])

    @patch(directory, 'logger', dummy_logger)
    def test_backup_setting_removed(self):
        Directory(name=self.tempdir, backup=True)
        self.assertEqual(dummy_logger.messages, [
            'WARNING: ``backup`` handling has been removed from '
            '``Directory`` implementation as of node.ext.directory 0.7'
        ])
        dummy_logger.clear()

        class DirectoryWithBackupFlagAsClassAttribute(Directory):
            backup = False

        DirectoryWithBackupFlagAsClassAttribute(
            name=self.tempdir,
            backup=True
        )
        self.assertEqual(dummy_logger.messages, [
            'WARNING: ``backup`` handling has been removed from '
            '``Directory`` implementation as of node.ext.directory 0.7'
        ])

    def test_node_index(self):
        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        self.assertEqual(len(directory._index), 1)

        directory['file.txt'] = File()
        self.assertEqual(len(directory._index), 2)

        subdir = directory['subdir'] = Directory()
        self.assertEqual(len(directory._index), 3)

        subdir['subfile.txt'] = File()
        self.assertEqual(len(directory._index), 4)

        directory()
        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        self.check_output("""\
        <class 'node.ext.directory.directory.Directory'>: ...root
          <class 'node.ext.directory.directory.File'>: file.txt
          <class 'node.ext.directory.directory.Directory'>: subdir
            <class 'node.ext.directory.directory.File'>: subfile.txt
        """, directory.treerepr())

        self.assertEqual(len(directory._index), 4)
        del directory['subdir']['subfile.txt']
        self.assertEqual(len(directory._index), 3)
        del directory['subdir']
        self.assertEqual(len(directory._index), 2)

        directory()
        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        self.check_output("""\
        <class 'node.ext.directory.directory.Directory'>: ...root
          <class 'node.ext.directory.directory.File'>: file.txt
        """, directory.treerepr())

        self.assertEqual(len(directory._index), 2)

    def test_lifecycle_events(self):
        # XXX: Currently file added event is triggered for both IFile and
        #      IDirectory implementing instance, it also gets triggered for
        #      existing files and directories on __getitem__. Further lifecycle
        #      events are only triggered on __setitem__
        # - Adopt code that node.behaviors.Lifecycle is used
        # - Suppress events on __getitem__?
        self.handler.clear()
        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        directory['file.txt'] = File()
        subdir = directory['subdir'] = Directory()
        self.assertEqual(len(self.handler.handled), 2)
        self.assertEqual(self.handler.handled[0].object.name, 'file.txt')
        self.assertTrue(IFileAddedEvent.providedBy(self.handler.handled[0]))
        self.assertEqual(self.handler.handled[1].object.name, 'subdir')
        self.assertTrue(IFileAddedEvent.providedBy(self.handler.handled[1]))


if __name__ == '__main__':
    unittest.main()                                           # pragma no cover
