from typing import Awaitable, Generic, Type, Callable, Union

from messenger.helpers.pubsub.event_aggregator import EventAggregator
from messenger.helpers.pubsub.subscription import Subscription
from messenger.constants.generics import B


class Subscriber(Generic[B]):
    def __init__(
        self,
        action_params_type: Type[B],
        action: Callable[[B], Union[Awaitable[None], None]],
        event_aggregator: EventAggregator,
    ):
        self.action_params_type = action_params_type
        self.action = action
        self.event_aggregator = event_aggregator

    def subscribe(self) -> Subscription[B]:
        self.event_aggregator.subscribe(self.action_params_type, self.action)
        return Subscription(
            self.action_params_type, self.action, self.event_aggregator
        )
