from node.base import BaseNode
from node.behaviors import Adopt
from node.behaviors import DefaultInit
from node.behaviors import DictStorage
from node.behaviors import Nodify
from node.behaviors import Reference
from node.compat import IS_PY2
from node.ext.directory.events import FileAddedEvent
from node.ext.directory.interfaces import IDirectory
from node.ext.directory.interfaces import IFile
from node.ext.directory.interfaces import MODE_BINARY
from node.ext.directory.interfaces import MODE_TEXT
from node.interfaces import IRoot
from node.locking import TreeLock
from node.locking import locktree
from plumber import Behavior
from plumber import default
from plumber import finalize
from plumber import plumbing
from zope.component.event import objectEventNotify
from zope.interface import alsoProvides
from zope.interface import implementer
import logging
import os
import shutil


logger = logging.getLogger('node.ext.directory')


def _fs_path(ob):
    # Use fs_path if provided by ob, otherwise fallback to path
    if hasattr(ob, 'fs_path'):
        return ob.fs_path
    return ob.path


def _fs_mode(ob):
    fs_path = os.path.join(*_fs_path(ob))
    if not os.path.exists(fs_path):
        return None
    return os.stat(fs_path).st_mode & 0o777


class _FSModeMixin(Behavior):

    @property
    def fs_mode(self):
        if not hasattr(self, '_fs_mode'):
            fs_mode = _fs_mode(self)
            if fs_mode is None:
                return None
            self._fs_mode = fs_mode
        return self._fs_mode

    @default
    @fs_mode.setter
    def fs_mode(self, mode):
        self._fs_mode = mode


@implementer(IFile)
class FileStorage(DictStorage, _FSModeMixin):
    direct_sync = default(False)

    @property
    def mode(self):
        if not hasattr(self, '_mode'):
            self.mode = MODE_TEXT
        return self._mode

    @default
    @mode.setter
    def mode(self, mode):
        self._mode = mode

    @property
    def data(self):
        if not hasattr(self, '_data'):
            if self.mode == MODE_BINARY:
                self._data = None
            else:
                self._data = ''
            file_path = os.path.join(*_fs_path(self))
            if os.path.exists(file_path):
                mode = self.mode == MODE_BINARY and 'rb' or 'r'
                with open(file_path, mode) as file:
                    self._data = file.read()
        return self._data

    @default
    @data.setter
    def data(self, data):
        setattr(self, '_changed', True)
        self._data = data

    @property
    def lines(self):
        if self.mode == MODE_BINARY:
            raise RuntimeError('Cannot read lines from binary file.')
        if not self.data:
            return []
        return self.data.split('\n')

    @default
    @lines.setter
    def lines(self, lines):
        if self.mode == MODE_BINARY:
            raise RuntimeError('Cannot write lines to binary file.')
        self.data = '\n'.join(lines)

    @default
    @property
    def fs_path(self):
        # seems more appropriate here:
        #     return self.parent.fs_path + [self.name]
        return self.path

    @finalize
    @locktree
    def __call__(self):
        file_path = os.path.join(*_fs_path(self))
        exists = os.path.exists(file_path)
        # Only write file if it's data has changed or not exists yet
        if hasattr(self, '_changed') or not exists:
            write_mode = self.mode == MODE_BINARY and 'wb' or 'w'
            with open(file_path, write_mode) as file:
                file.write(self.data)
                if self.direct_sync:
                    file.flush()
                    os.fsync(file.fileno())
        # Change file system mode if set
        fs_mode = self.fs_mode
        if fs_mode is not None:
            os.chmod(file_path, fs_mode)


@plumbing(
    Adopt,
    DefaultInit,
    Reference,  # XXX: remove from default file
    Nodify,
    FileStorage)
class File(object):
    pass


# global file factories
file_factories = dict()


@implementer(IDirectory)
class DirectoryStorage(DictStorage, _FSModeMixin):
    fs_encoding = default('utf-8')
    ignores = default(list())
    default_file_factory = default(File)

    # XXX: rename later to file_factories, keep now as is for B/C reasons
    factories = default(dict())

    @default
    @property
    def file_factories(self):
        # temporary, see above
        return self.factories

    @default
    @property
    def child_directory_factory(self):
        return Directory

    @default
    @property
    def fs_path(self):
        return self.path

    @finalize
    def __init__(self, name=None, parent=None, backup=False, factories=dict()):
        self.__name__ = name
        self.__parent__ = parent
        if backup or hasattr(self, 'backup'):
            logger.warning(
                '``backup`` handling has been removed from ``Directory`` '
                'implementation as of node.ext.directory 0.7')
        # override file factories if given
        if factories:
            self.factories = factories
        self._deleted = list()

    @finalize
    @locktree
    def __call__(self):
        if IDirectory.providedBy(self):
            dir_path = os.path.join(*self.fs_path)
            if os.path.exists(dir_path) and not os.path.isdir(dir_path):
                raise KeyError(
                    'Attempt to create a directory with name which already '
                    'exists as file')
            try:
                os.mkdir(dir_path)
            except OSError as e:
                # Ignore ``already exists``.
                if e.errno != 17:
                    raise e                                   # pragma no cover
            # Change file system mode if set
            fs_mode = self.fs_mode
            if fs_mode is not None:
                os.chmod(dir_path, fs_mode)
        while self._deleted:
            name = self._deleted.pop()
            abs_path = os.path.join(*self.fs_path + [name])
            if os.path.exists(abs_path):
                if os.path.isdir(abs_path):
                    shutil.rmtree(abs_path)
                else:
                    os.remove(abs_path)
        for name, target in self.items():
            if IDirectory.providedBy(target):
                target()
            elif IFile.providedBy(target):
                target()

    @finalize
    def __setitem__(self, name, value):
        if not name:
            raise KeyError('Empty key not allowed in directories')
        name = self._encode_name(name)
        if IFile.providedBy(value) or IDirectory.providedBy(value):
            self.storage[name] = value
            # XXX: This event is currently used in node.ext.zcml and
            #      node.ext.python to trigger parsing. But this behavior
            #      requires the event to be triggered on __getitem__ which is
            #      actually not how life cycle events shall behave. Fix in
            #      node.ext.zcml and node.ext.python, remove event notification
            #      here, use node.behaviors.Lifecycle and suppress event
            #      notification in self._create_child_by_factory
            objectEventNotify(FileAddedEvent(value))
            return
        raise ValueError('Unknown child node.')

    @finalize
    def __getitem__(self, name):
        name = self._encode_name(name)
        try:
            return self.storage[name]
        except KeyError:
            self._create_child_by_factory(name)
        return self.storage[name]

    @default
    @locktree
    def _create_child_by_factory(self, name):
        filepath = os.path.join(*self.fs_path + [name])
        if not os.path.exists(filepath):
            return
        if os.path.isdir(filepath):
            # XXX: to suppress event notify
            self[name] = self.child_directory_factory()
            return
        factory = self._factory_for_ending(name)
        if not factory:
            # XXX: to suppress event notify
            self[name] = self.default_file_factory()
            return
        try:
            # XXX: to suppress event notify
            self[name] = factory()
        except TypeError as e:
            # happens if the factory cannot be called without args, in this
            # case we treat it as a flat file.
            # XXX: to suppress event notify
            logger.error(
                'File creation by factory failed. Fall back to ``File``. '
                'Reason: {}'.format(e))
            self[name] = File()

    @finalize
    def __delitem__(self, name):
        name = self._encode_name(name)
        if os.path.exists(os.path.join(*self.fs_path + [name])):
            self._deleted.append(name)
        del self.storage[name]

    @finalize
    def __iter__(self):
        try:
            existing = set(os.listdir(os.path.join(*self.fs_path)))
        except OSError:
            existing = set()
        for key in self.storage:
            existing.add(key)
        for key in existing:
            if key in self._deleted:
                continue
            if key in self.ignores:
                continue
            yield key

    @default
    def _encode_name(self, name):
        name = name.encode(self.fs_encoding) \
            if IS_PY2 and isinstance(name, unicode) \
            else name
        return name

    @default
    def _factory_for_ending(self, name):
        def match(keys, key):
            keys = sorted(
                keys,
                key=lambda x: len(x),
                reverse=True
            )
            for possible in keys:
                if key.endswith(possible):
                    return possible
        factory_keys = [
            match(self.file_factories.keys(), name),
            match(file_factories.keys(), name),
        ]
        if factory_keys[0]:
            if factory_keys[1] and len(factory_keys[1]) > len(factory_keys[0]):
                return file_factories[factory_keys[1]]
            return self.file_factories[factory_keys[0]]
        if factory_keys[1]:
            return file_factories[factory_keys[1]]


@plumbing(
    Adopt,
    Reference,  # XXX: remove from default file
    Nodify,
    DirectoryStorage)
class Directory(object):
    """Object mapping a file system directory.
    """
