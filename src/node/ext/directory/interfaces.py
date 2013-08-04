from zope.interface import Attribute
from zope.lifecycleevent import IObjectAddedEvent
from node.interfaces import (
    ILeaf,
    ICallable,
)


class IFileAddedEvent(IObjectAddedEvent):
    """An File has been added to directory.
    """


class IFile(ICallable, ILeaf):
    """Marker interface for a file.
    """


class IDirectory(ICallable):
    """Directory target interface.
    """

    backup = Attribute(u"Create backup files of handled files. Defaults "
                        "to False")

    child_directory_factory = Attribute(u"Factory creating concrete node "
                                        u"instances for directory children")

    def __setitem__(name, value):
        """Set item inside this directory.

        @param name: name of the item (either a file name or a directory name)
        
        @param value: either ``IFile`` implementation or None. If
                      value is None, create ``IDirectory`` child.
        
        @raise ValueError: If child for name already set.
        """
