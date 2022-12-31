from typing import Tuple
from unittest.mock import MagicMock
import pytest
from pytest_mock import MockerFixture
from messenger.helpers.pubsub.subscription import Subscription
from tests.helpers.pubsub.conftest import EventParams1


class TestSubscription:
    @pytest.fixture
    def setup_subscription(self, mocker: MockerFixture):
        event_aggregator_mock = mocker.MagicMock()
        event_mock = mocker.MagicMock()

        subscription = Subscription(
            EventParams1, event_mock, event_aggregator_mock
        )

        return event_aggregator_mock, event_mock, subscription

    def test_unsubscribes_from_event_aggregator(
        self, setup_subscription: Tuple[MagicMock, MagicMock, Subscription]
    ):
        event_aggregator_mock, _, subscription = setup_subscription

        subscription.unsubscribe()

        event_aggregator_mock.unsubscribe.assert_called_once_with(subscription)
