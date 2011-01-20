from plumber import Plumber
import os
import shutil
from node.base import BaseNode
from node.plumbing.reference import Reference
from node.interfaces import IRoot
from zope.interface import implements
from zope.interface import alsoProvides
from zope.component.event import objectEventNotify
from node.ext.directory.interfaces import IDirectory
from node.ext.directory.interfaces import IFile
from node.ext.directory.events import FileAddedEvent

class Directory(BaseNode):
    __metaclass__ = Plumber
    __pipeline__ = Reference
    """Object mapping a file system directory.
    """

    implements(IDirectory)

    def __init__(self, name=None, backup=False):
        super(Directory, self).__init__(name)
        self.backup = backup

    __repr__ = object.__repr__

    def __call__(self):
        if self.__parent__:
            if hasattr(self, '_from_root'):
                if not self._from_root:
                        raise RuntimeError(u"Directory called but not on "
                                            "virtual root.")
        if IRoot.providedBy(self):
            setattr(self, '_from_root', True)
        if IDirectory.providedBy(self):
            self._mkdir()
        for name, target in self.items():
            if IDirectory.providedBy(target):
                target()
            elif IFile.providedBy(target):
                if self.backup and os.path.exists(target.abspath):
                    shutil.copyfile(target.abspath, target.abspath + '.bak')
                target()
        if IRoot.providedBy(self):
            setattr(self, '_from_root', False)

    def markroot(self):
        """Mark this directory as root.
        """
        if self.__parent__:
            raise RuntimeError(u"Could not mark virtual child as root.")
        alsoProvides(self, IRoot)

    @property
    def abspath(self):
        return os.path.sep.join(self.path)

    def _mkdir(self):
        try:
            os.mkdir(self.abspath)
        except OSError, e:
            # Ignore ``already exists``.
            if e.errno != 17:
                raise

    def __setitem__(self, name, value):
        if name in self.keys():
            msg = u"Node already exists: %s" % ('/'.join(self.path + [name]))
            raise ValueError(msg)
        if value is None:
            value = Directory(backup=self.backup)
            super(Directory, self).__setitem__(name, value)
        elif IFile.providedBy(value) \
          or IDirectory.providedBy(value):
            super(Directory, self).__setitem__(name, value)
        objectEventNotify(FileAddedEvent(value))

    def __getitem__(self, name):
        if not name in self.keys():
            value = Directory(backup=self.backup)
            super(Directory, self).__setitem__(name, value)
        return super(Directory, self).__getitem__(name)

    def _get_child_files(self):
        """Get the directly contained template handlers.

        Returns (name, handler) tuples.
        """
        return [(name, handler) for (name, handler) in self.items()
                if IFile.providedBy(handler)]

    def _get_child_dirs(self):
        """Get the directly contained directory handlers.

        Returns (name, handler) tuples.
        """
        return [(name, handler) for (name, handler) in self.items()
                if IDirectory.providedBy(handler)]

    def _print_tree(self, level=0):
        """Return a string representation of the contained directory tree.
        """
        ret = ""
        if level == 0:
            ret += '/'.join(self.path) + "\n"
        for name, handler in self._get_child_files():
            ret += level * "    " + "|-- " + name + "\n"
        for name, handler in self._get_child_dirs():
            ret += level * "    " + "`-- " + name + "\n"
            ret += handler._print_tree(level+1)
        return ret

    def __str__(self):
        return self._print_tree()
