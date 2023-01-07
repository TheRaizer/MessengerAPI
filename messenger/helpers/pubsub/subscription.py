from typing import Awaitable, Callable, Generic, Type, Union

from messenger.helpers.pubsub.event_aggregator import EventAggregator
from messenger.constants.generics import B


class Subscription(Generic[B]):
    def __init__(
        self,
        action_param_type: Type[B],
        action: Callable[[B], Union[Awaitable[None], None]],
        event_aggregator: EventAggregator,
    ):
        self.action_param_type = action_param_type
        self.action = action
        self.event_aggregator = event_aggregator

    def unsubscribe(self):
        self.event_aggregator.unsubscribe(self)
