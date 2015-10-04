from node.interfaces import ICallable
from node.interfaces import ILeaf
from node.interfaces import INode
from zope.interface import Attribute
from zope.lifecycleevent import IObjectAddedEvent


class IFileAddedEvent(IObjectAddedEvent):
    """An File has been added to directory.
    """


class IFile(INode, ILeaf, ICallable):
    """Marker interface for a file.
    """


class IDirectory(INode, ICallable):
    """Directory target interface.
    """

    backup = Attribute(u"Create backup files of handled files. Defaults "
                        "to False")

    child_directory_factory = Attribute(u"Factory creating concrete node "
                                        u"instances for directory children")

    default_file_factory = Attribute(u"Default factory creating concrete node "
                                     u"instances for file children")

    file_factories = Attribute(u"Dict containing file names or endings as "
                               u"keys with the corresponding file node "
                               u"creating factory.")

    ignores = Attribute(u"child keys to ignore")
