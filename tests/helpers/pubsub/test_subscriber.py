from typing import Tuple
from unittest.mock import MagicMock
import pytest
from pytest_mock import MockerFixture
from messenger.helpers.pubsub.subscriber import Subscriber
from tests.helpers.pubsub.conftest import EventParams1


class TestSubscriber:
    @pytest.fixture
    def setup_subscriber(self, mocker: MockerFixture):
        event_aggregator_mock = mocker.MagicMock()
        event_mock = mocker.MagicMock()

        subscriber = Subscriber(EventParams1, event_mock, event_aggregator_mock)

        return event_aggregator_mock, event_mock, subscriber

    def test_subscribes_to_event_aggregator(
        self, setup_subscriber: Tuple[MagicMock, MagicMock, Subscriber]
    ):
        event_aggregator_mock, event_mock, subscriber = setup_subscriber

        subscriber.subscribe()

        event_aggregator_mock.subscribe.assert_called_once_with(
            EventParams1, event_mock
        )

    def test_generates_subscription_when_subscribed(
        self, setup_subscriber: Tuple[MagicMock, MagicMock, Subscriber]
    ):
        event_aggregator_mock, event_mock, subscriber = setup_subscriber

        subscription = subscriber.subscribe()

        assert subscription.action is event_mock
        assert subscription.action_param_type == EventParams1
        assert subscription.event_aggregator == event_aggregator_mock
