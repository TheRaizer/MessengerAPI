from typing import Any, List, Tuple
from unittest.mock import MagicMock
import pytest
from pytest_mock import MockerFixture
from messenger.helpers.pubsub.event_aggregator import EventAggregator
from messenger.helpers.pubsub.subscriber import Subscriber
from tests.helpers.pubsub.conftest import (
    EventParams1,
    EventParams2,
    EventParams3,
)


@pytest.mark.asyncio
class TestSubscribedEvents:
    @pytest.fixture
    def setup_subscriptions(self, mocker: MockerFixture):
        event_aggregator = EventAggregator()

        event_1_mock = mocker.MagicMock()
        event_2_mock = mocker.MagicMock()
        event_3_mock = mocker.MagicMock()
        event_4_mock = mocker.MagicMock()

        event_aggregator.subscribe(EventParams1, event_1_mock)
        event_aggregator.subscribe(EventParams1, event_3_mock)

        event_aggregator.subscribe(EventParams2, event_2_mock)
        event_aggregator.subscribe(EventParams3, event_4_mock)

        events = [
            (EventParams1, [event_1_mock, event_3_mock]),
            (EventParams2, [event_2_mock]),
            (EventParams3, [event_4_mock]),
        ]

        yield events, event_aggregator

        event_aggregator._events.clear()

    async def test_subscriptions_are_published_with_correct_arguments(
        self,
        setup_subscriptions: Tuple[
            List[Tuple[Any, List[MagicMock]]], EventAggregator
        ],
    ):
        events, event_aggregator = setup_subscriptions

        for EventParams, event_mocks in events:
            event_params = EventParams()
            for event_mock in event_mocks:
                assert event_mock.call_count == 0

            await event_aggregator.publish(event_params)

            for event_mock in event_mocks:
                assert event_mock.called_once_with(event_params)

    async def test_subscriptions_are_unsubscribed(
        self,
        mocker: MockerFixture,
    ):
        event_aggregator = EventAggregator()

        event_1_mock = mocker.MagicMock()
        event_2_mock = mocker.MagicMock()

        subscriber_1 = Subscriber(EventParams1, event_1_mock, event_aggregator)
        subscriber_2 = Subscriber(EventParams2, event_2_mock, event_aggregator)

        subscription_1 = subscriber_1.subscribe()
        subscription_2 = subscriber_2.subscribe()

        event_aggregator.unsubscribe(subscription_1)
        await event_aggregator.publish(EventParams1())
        assert event_1_mock.call_count == 0

        event_aggregator.unsubscribe(subscription_2)
        await event_aggregator.publish(EventParams2())
        assert event_2_mock.call_count == 0

    async def test_all_subscriptions_are_unsubscribed(
        self,
        setup_subscriptions: Tuple[
            List[Tuple[Any, List[MagicMock]]], EventAggregator
        ],
    ):
        events, event_aggregator = setup_subscriptions

        for EventParams, _ in events:
            event_params = EventParams()
            event_aggregator.clear_subscriptions(EventParams)

            with pytest.raises(KeyError):
                await event_aggregator.publish(event_params)
