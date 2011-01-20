# Copyright BlueDynamics Alliance - http://bluedynamics.com
# GNU General Public License Version 2

from zope.interface import Attribute
from zope.lifecycleevent import IObjectAddedEvent
from zodict.interfaces import ILeaf
from zodict.interfaces import ICallableNode

class IFileAddedEvent(IObjectAddedEvent):
    """An File has been added to directory.
    """

class IFile(ICallableNode, ILeaf):
    """Marker interface for a file.
    """

class IDirectory(ICallableNode):
    """Directory target interface.
    """

    backup = Attribute(u"Create backup files of handled files. Defaults "
                        "to False")

    def __setitem__(name, value):
        """Set item inside this directory.

        @param name: name of the item (either a file name or a directory name)
        @param value: either ``IFile`` implementation or None. If
                      value is None, create ``IDirectory`` child.
        @raise ValueError: If child for name already set.
        """
