from zope.interface import implements
from zope.lifecycleevent import ObjectAddedEvent
from agx.io.directory.interfaces import IFileAddedEvent

class FileAddedEvent(ObjectAddedEvent):
    implements(IFileAddedEvent)
