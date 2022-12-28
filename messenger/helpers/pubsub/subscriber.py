from typing import Awaitable, Generic, Type, TypeVar, Callable, Union

from pydantic import BaseModel

from messenger.helpers.pubsub.event_aggregator import EventAggregator
from messenger.helpers.pubsub.subscription import Subscription

T = TypeVar("T", bound=BaseModel)


class Subscriber(Generic[T]):
    def __init__(
        self,
        action_params_type: Type[T],
        action: Callable[[T], Union[Awaitable[None], None]],
        event_aggregator: EventAggregator,
    ):
        self.action_params_type = action_params_type
        self.action = action
        self.event_aggregator = event_aggregator

    def subscribe(self) -> Subscription[T]:
        self.event_aggregator.subscribe(self.action_params_type, self.action)
        return Subscription(
            self.action_params_type, self.action, self.event_aggregator
        )
