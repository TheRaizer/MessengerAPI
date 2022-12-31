"""
Here we define event params which are used to define event types.
As well as an event aggregator which will allow us to publish and
subscribe events to happen on connection and disconnection of the socket.

This avoids the need to continuously modify the base connect and disconnect
events. Instead when we want to do something on connect and disconnect, we can
subscribe to the event through the socket_event_aggregator.
"""
from pydantic import BaseModel

from messenger.helpers.pubsub.event_aggregator import EventAggregator


class OnConnectionParams(BaseModel):
    sid: str
    current_user_id: int


class OnDisconnectionParams(BaseModel):
    sid: str


socket_event_aggregator = EventAggregator()
