"""
Here we define an event aggregator which will allow us to publish and
subscribe events to happen on connection and disconnection of the socket.

This avoids the need to continuously modify the base connect and disconnect
events. Instead when we want to do something on connect and disconnect, we can
subscribe to the event through the socket_event_aggregator.
"""

from messenger.helpers.pubsub.event_aggregator import EventAggregator


socket_event_aggregator = EventAggregator()
