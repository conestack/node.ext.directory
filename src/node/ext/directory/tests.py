# -*- coding: utf-8 -*-
from node.behaviors import Adopt
from node.behaviors import DefaultInit
from node.behaviors import DictStorage
from node.behaviors import Nodify
from node.behaviors import Reference
from node.ext.directory import Directory
from node.ext.directory import File
from node.ext.directory import MODE_BINARY
from node.ext.directory import MODE_TEXT
from node.ext.directory import directory
from node.tests import NodeTestCase
from node.tests import patch
from plumber import plumbing
import logging
import node.ext.directory
import os
import shutil
import tempfile


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

    def debug(self, message):
        self.log(logging.DEBUG, message)

    def info(self, message):
        self.log(logging.INFO, message)

    def warning(self, message):
        self.log(logging.WARNING, message)

    def error(self, message):
        self.log(logging.ERROR, message)


dummy_logger = DummyLogger()


class TestDirectory(NodeTestCase):

    def setUp(self):
        super(TestDirectory, self).setUp()
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        super(TestDirectory, self).tearDown()
        dummy_logger.clear()
        shutil.rmtree(self.tempdir)

    def test_file_persistance(self):
        filepath = os.path.join(self.tempdir, 'file.txt')
        file = File(filepath)
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
        file = File(filepath)
        file.direct_sync = True

        self.assertEqual(file.mode, MODE_TEXT)
        self.assertEqual(file.data, '')
        self.assertEqual(file.lines, [])

        file.data = 'abc\ndef'
        file()
        with open(filepath) as f:
            out = f.readlines()
        self.assertEqual(out, ['abc\n', 'def'])

        file = File(filepath)
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

        file = BinaryFile(filepath)
        self.assertEqual(file.data, None)

        err = self.expect_error(RuntimeError, lambda: file.lines)
        self.assertEqual(str(err), 'Cannot read lines from binary file.')

        def set_lines_fails():
            file.lines = []
        err = self.expect_error(RuntimeError, set_lines_fails)
        self.assertEqual(str(err), 'Cannot write lines to binary file.')

        file.data = '\x00\x00'
        file()
        with open(filepath) as f:
            out = f.read()
        self.assertEqual(out, '\x00\x00')

    def test_file_permissions(self):
        filepath = os.path.join(self.tempdir, 'file.txt')
        file = File(filepath)
        file.fs_mode = 0644
        file.direct_sync = True

        file()
        self.assertTrue(os.path.exists(filepath))
        self.assertEqual(oct(os.stat(filepath).st_mode & 0777), '0644')

        file.fs_mode = 0600
        file()
        self.assertEqual(oct(os.stat(filepath).st_mode & 0777), '0600')

    def test_file_with_unicode_name(self):
        directory = Directory(name=self.tempdir)
        directory[u'ä'] = File()
        directory()
        self.assertEqual(os.listdir(self.tempdir), ['\xc3\xa4'])

        directory = Directory(name=self.tempdir)
        expected = '<File object \'ä\' at '
        self.assertTrue(str(directory[u'ä']).startswith(expected))

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
            pass

        def dummy_foo_factory():
            pass

        node.ext.directory.file_factories['.txt'] = dummy_txt_factory
        node.ext.directory.file_factories['foo.txt'] = dummy_foo_factory
        self.assertEqual(dir._factory_for_ending('bar.txt'), dummy_txt_factory)
        self.assertEqual(dir._factory_for_ending('foo.txt'), dummy_foo_factory)

        def dummy_local_txt_factory():
            pass

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
            pass

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
            return SaneFile()

        directory = Directory(name=self.tempdir, factories={
            '.txt': broken_factory
        })
        expected = '<File object \'file.txt\' at '
        self.assertTrue(str(directory['file.txt']).startswith(expected))
        self.assertEqual(dummy_logger.messages, [
            'ERROR: File creation by factory failed. Fall back to ``File``. '
            'Reason: broken_factory() takes exactly 1 argument (0 given)'
        ])

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

        directory.fs_mode = 0750
        directory()
        self.assertEqual(oct(os.stat(dirpath).st_mode & 0777), '0750')

        directory.fs_mode = 0700
        directory()
        self.assertEqual(oct(os.stat(dirpath).st_mode & 0777), '0700')

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
        directory.fs_mode = 0777

        subdir1 = directory['subdir1'] = Directory()
        subdir1.fs_mode = 0770

        subdir2 = directory['subdir2'] = Directory()
        subdir2.fs_mode = 0755

        directory()

        dir_path = os.path.join(*directory.fs_path)
        self.assertEqual(oct(os.stat(dir_path).st_mode & 0777), '0777')

        subdir1_path = os.path.join(*subdir1.fs_path)
        self.assertEqual(oct(os.stat(subdir1_path).st_mode & 0777), '0770')

        subdir2_path = os.path.join(*subdir2.fs_path)
        self.assertEqual(oct(os.stat(subdir2_path).st_mode & 0777), '0755')

        # XXX: read directory again, permission should be read from file system
        #      if fs_mode not set explicitely
        directory = Directory(name=os.path.join(self.tempdir, 'root'))
        self.assertEqual(directory.fs_mode, None)

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


if __name__ == '__main__':
    unittest.main()                                           # pragma no cover
