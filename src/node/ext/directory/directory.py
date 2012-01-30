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
    
    def _get_data(self):
        if not hasattr(self, '_data'):
            self._data = ''
            if os.path.exists(os.path.sep.join(self.path)):
                with open(os.path.sep.join(self.path), 'r') as file:
                    self._data = file.read()
        return self._data
    
    def _set_data(self, data):
        self._data = data
    
    data = property(_get_data, _set_data)
    
    def _get_lines(self):
        return self.data.split('\n')
    
    def _set_lines(self, lines):
        self.data = '\n'.join(lines)
    
    lines = property(_get_lines, _set_lines)
    
    def __call__(self):
        with open(os.path.sep.join(self.path), 'w') as file:
            file.write(self.data)


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
    
    def __init__(self, name=None, parent=None,
                 backup=True, factories=file_factories):
        self.__name__ = name
        self.__parent__ = parent
        self.backup = backup
        self.file_factories = file_factories
        self._deleted = list()

    def __call__(self):
        if IDirectory.providedBy(self):
            try:
                os.mkdir(os.path.join(*self.path))
            except OSError, e:
                # Ignore ``already exists``.
                if e.errno != 17:
                    raise
        for name in self._deleted:
            abspath = os.path.join(*self.path + [name])
            if os.path.exists(abspath):
                if os.path.isdir(abspath):
                    shutil.rmtree(abspath)
                else:
                    os.remove(abspath)
                    if os.path.exists(abspath + '.bak'):
                        os.remove(abspath + '.bak')
                continue
        for name, target in self.items():
            if IDirectory.providedBy(target):
                target()
            elif IFile.providedBy(target):
                target()
                abspath = os.path.join(*target.path)
                if self.backup and os.path.exists(abspath):
                    shutil.copyfile(abspath, abspath + '.bak')

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
                        raise ValueError(
                            u"Found but no factory registered: %s" % name)
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
        for key in self.file_factories.keys():
            if name.endswith(key):
                return self.file_factories[key]