from typing import Awaitable, Callable, Generic, Type, TypeVar, Union

from pydantic import BaseModel

from messenger.helpers.pubsub.event_aggregator import EventAggregator


T = TypeVar("T", bound=BaseModel)


class Subscription(Generic[T]):
    def __init__(
        self,
        action_param_type: Type[T],
        action: Callable[[T], Union[Awaitable[None], None]],
        event_aggregator: EventAggregator,
    ):
        self.action_param_type = action_param_type
        self.action = action
        self.event_aggregator = event_aggregator

    def unsubscribe(self):
        self.event_aggregator.unsubscribe(self)
