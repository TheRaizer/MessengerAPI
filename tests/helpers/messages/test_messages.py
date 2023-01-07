from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock, patch
from freezegun import freeze_time
import pytest
from pytest_mock import MockerFixture
from messenger_schemas.schema.message_schema import (
    MessageSchema,
)

from messenger.helpers.handlers.message_handler import MessageHandler
from tests.helpers.messages import FROZEN_DATE


@freeze_time(FROZEN_DATE)
@pytest.mark.parametrize(
    "sender_id, reciever_id, content, group_chat_id",
    [
        (1, None, "hi there", 1),
        (532, 233, "this is some content", None),
        (221, 12, "", None),
        (2332, None, "this is a message to multiple people", 231),
    ],
)
@patch("messenger.helpers.handlers.message_handler.MessageSchema")
@patch("messenger.helpers.handlers.message_handler.datetime")
def test_send_message(
    datetime_mock: MagicMock,
    MessageSchemaMock: MagicMock,
    mocker: MockerFixture,
    sender_id: int,
    reciever_id: Optional[int],
    content: str,
    group_chat_id: Optional[int],
):
    session_mock = mocker.MagicMock()
    datetime_mock.now.return_value = datetime.now()

    message_handler = MessageHandler(session_mock)

    kwargs = {
        "sender_id": sender_id,
        "reciever_id": reciever_id,
        "content": content,
        "created_date_time": datetime_mock.now.return_value,
        "group_chat_id": group_chat_id,
    }

    expected_message = MessageSchema(**kwargs)

    MessageSchemaMock.return_value = expected_message

    message = message_handler.send_message(
        sender_id, reciever_id, content, group_chat_id
    )

    # message record should be created, then added to database, commited, then refreshed.
    MessageSchemaMock.assert_called_once_with(**kwargs)

    session_mock.add.assert_called_once_with(expected_message)
    session_mock.commit.assert_called_once()
    session_mock.refresh.assert_called_once_with(expected_message)

    assert message is expected_message


@pytest.mark.parametrize(
    "criterion",
    [
        ((MessageSchema.group_chat_id == 1, MessageSchema.content == "hi")),
        ((MessageSchema.sender_id == 12)),
        ((MessageSchema.message_id == 451)),
        ((MessageSchema.group_chat_id == 1, MessageSchema.message_id == 12)),
    ],
)
@patch(
    "messenger.helpers.handlers.message_handler.MessageHandler._get_record_with_not_found_raise"
)
def test_get_message(
    _get_record_with_not_found_raise_mock: MagicMock,
    mocker: MockerFixture,
    criterion,
):
    session_mock = mocker.MagicMock()

    expected_message = MessageSchema(message_id=332)
    message_handler = MessageHandler(session_mock)

    _get_record_with_not_found_raise_mock.return_value = expected_message
    message = message_handler.get_message(criterion)

    # should call _get_record_with_not_found_raise with these parameters in
    # order to retrieve the correct message record.
    _get_record_with_not_found_raise_mock.assert_called_once_with(
        MessageSchema, "no such message exists", criterion
    )

    assert message is expected_message
    assert message_handler.message is expected_message
