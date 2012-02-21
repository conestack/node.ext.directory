import os
import shutil
from plumber import plumber
from node.base import BaseNode
from node.parts import (
    NodeChildValidate,
    Adopt,
    AsAttrAccess,
    DefaultInit,
    Reference,
    Nodify,
    DictStorage,
)
from node.interfaces import IRoot
from zope.interface import (
    implements,
    alsoProvides,
)
from zope.component.event import objectEventNotify
from node.ext.directory.interfaces import (
    IDirectory,
    IFile,
)
from node.ext.directory.events import FileAddedEvent


MODE_TEXT = 0
MODE_BINARY = 1


class File(object):
    __metaclass__ = plumber
    __plumbing__ = (
        Adopt,
        DefaultInit,
        Reference,
        Nodify,
        DictStorage,
    )
    implements(IFile)
    
    def _get_mode(self):
        if not hasattr(self, '_mode'):
            self._mode = MODE_TEXT
        return self._mode
    
    def _set_mode(self):
        self._mode = mode
    
    mode = property(_get_mode, _set_mode)
    
    def _get_data(self):
        if not hasattr(self, '_data'):
            if self.mode == MODE_BINARY:
                self._data = None
            else:
                self._data = ''
            if os.path.exists(os.path.sep.join(self.path)):
                mode = self.mode == MODE_BINARY and 'rb' or 'r'
                with open(os.path.sep.join(self.path), mode) as file:
                    self._data = file.read()
        return self._data
    
    def _set_data(self, data):
        setattr(self, '_changed', True)
        self._data = data
    
    data = property(_get_data, _set_data)
    
    def _get_lines(self):
        if self.mode == MODE_BINARY:
            raise RuntimeError(u"Cannot read lines from binary file.")
        return self.data.split('\n')
    
    def _set_lines(self, lines):
        if self.mode == MODE_BINARY:
            raise RuntimeError(u"Cannot write lines to binary file.")
        self.data = '\n'.join(lines)
    
    lines = property(_get_lines, _set_lines)
    
    def __call__(self):
        exists = os.path.exists(os.path.join(*self.path))
        if not hasattr(self, '_changed') and exists:
            # do not overwrite file if not changed. if not exists but set
            # and empty, write empty file. 
            return
        mode = self.mode == MODE_BINARY and 'wb' or 'w'
        with open(os.path.join(*self.path), mode) as file:
            file.write(self.data)


# global file factories
file_factories = dict()


class Directory(object):
    """Object mapping a file system directory.
    """
    __metaclass__ = plumber
    __plumbing__ = (
        NodeChildValidate,
        Adopt,
        DefaultInit,
        Reference,
        Nodify,
        DictStorage,
    )
    implements(IDirectory)
    backup = True
    
    def __init__(self, name=None, parent=None, backup=False, factories=dict()):
        self.__name__ = name
        self.__parent__ = parent
        self.backup = backup
        # local file factories, overrule global factories
        self.factories = factories
        self._deleted = list()

    def __call__(self):
        if IDirectory.providedBy(self):
            try:
                os.mkdir(os.path.join(*self.path))
            except OSError, e:
                # Ignore ``already exists``.
                if e.errno != 17:
                    raise e
        for name in self._deleted:
            abspath = os.path.join(*self.path + [name])
            if os.path.exists(abspath):
                if os.path.isdir(abspath):
                    shutil.rmtree(abspath)
                else:
                    os.remove(abspath)
                    bakpath = os.path.join(*self.path + ['.%s.bak' % name])
                    if os.path.exists(bakpath):
                        os.remove(bakpath)
                continue
        for name, target in self.items():
            if IDirectory.providedBy(target):
                target()
            elif IFile.providedBy(target):
                target()
                abspath = os.path.join(*target.path)
                if self.backup and os.path.exists(abspath):
                    bakpath = os.path.join(
                        *target.path[:-1] + ['.%s.bak' % target.name])
                    shutil.copyfile(abspath, bakpath)

    def __setitem__(self, name, value):
        if IFile.providedBy(value) or IDirectory.providedBy(value):
            if IDirectory.providedBy(value):
                value.backup = self.backup
            self.storage[name] = value
            objectEventNotify(FileAddedEvent(value))
            return
        raise ValueError(u"Unknown child node.")

    def __getitem__(self, name):
        if not name in self.storage:
            filepath = os.path.join(*self.path + [name])
            if os.path.exists(filepath):
                if os.path.isdir(filepath):
                    self[name] = Directory()
                else:
                    factory = self._factory_for_ending(name)
                    if factory:
                        self[name] = factory()
                    else:
                        # default
                        self[name] = File()
        return self.storage[name]
    
    def __delitem__(self, name):
        if os.path.exists(os.path.join(*self.path + [name])):
            self._deleted.append(name)
        del self.storage[name]
    
    def __iter__(self):
        try:
            existing = set(os.listdir(os.path.join(*self.path)))
        except OSError:
            existing = set()
        for key in self.storage:
            existing.add(key)
        for key in existing:
            if self.backup and key.endswith('.bak'):
                continue
            if key in self._deleted:
                continue
            yield key
    
    def _factory_for_ending(self, name):
        def match(keys, key):
            keys = sorted(keys)
            keys = sorted(keys,
                          cmp=lambda x, y: len(x) > len(y) and 1 or -1,
                          reverse=True)
            for possible in keys:
                if key.endswith(possible):
                    return possible
        factory_keys = [
            match(self.factories.keys(), name),
            match(file_factories.keys(), name),
        ]
        if factory_keys[0]:
            if factory_keys[1] and len(factory_keys[1]) > len(factory_keys[0]):
                return file_factories[factory_keys[1]]
            return self.factories[factory_keys[0]]
        if factory_keys[1]:
            return file_factories[factory_keys[1]]