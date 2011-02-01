from zope.interface import implements
from zope.lifecycleevent import ObjectAddedEvent
from node.ext.directory.interfaces import IFileAddedEvent


class FileAddedEvent(ObjectAddedEvent):
    implements(IFileAddedEvent)
