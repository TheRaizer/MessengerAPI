from __future__ import annotations
import inspect

from typing import (
    Awaitable,
    Callable,
    Dict,
    List,
    Type,
    TYPE_CHECKING,
    Union,
    Any,
)

from messenger.constants.generics import B

if TYPE_CHECKING:
    from messenger.helpers.pubsub.subscription import Subscription


class EventAggregator:
    _events: Dict[
        Type, List[Callable[[Any], Union[Awaitable[None], None]]]
    ] = {}

    def subscribe(
        self,
        action_params_type: Type[B],
        action: Callable[[B], Union[Awaitable[None], None]],
    ) -> None:
        """Subscribes a given action to a certain event. This event
        is identified by the id() of the param type the action will recieve.

        Args:
            action_params_type (Type[T]): the parameter type to identify the event with
            action (Callable[[T], Union[Awaitable[None], None]]): the action to subscribe to a
            given event
        """
        key = id(action_params_type)
        if key not in self._events:
            self._events[id(action_params_type)] = []

        self._events[id(action_params_type)].append(action)

    async def publish(self, params: B):
        """Publishes all subscribers that are subscribed to the
        event: id(type(params)). Params is the instance of the event identifer type
        that will be fed as arguments to each subscribers action.

        Args:
            params (T): the parameters that the subscriber expected
            to recieve as arguments to its action.
        """
        for action in self._events[id(type(params))]:
            if inspect.iscoroutinefunction(action):
                await action(params)
            else:
                action(params)

    def unsubscribe(self, subscription: Subscription[B]):
        self._events[id(subscription.action_param_type)].remove(
            subscription.action
        )

    def clear_subscriptions(self, event_type: Type[B]):
        del self._events[id(event_type)]
