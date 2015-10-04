from node.ext.directory.interfaces import IFileAddedEvent
from zope.interface import implements
from zope.lifecycleevent import ObjectAddedEvent


class FileAddedEvent(ObjectAddedEvent):
    implements(IFileAddedEvent)
