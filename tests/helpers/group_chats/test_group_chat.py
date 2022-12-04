from unittest.mock import MagicMock, patch
import pytest
from pytest_mock import MockerFixture
from _submodules.messenger_utils.messenger_schemas.schema.group_chat_schema import (
    GroupChatSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.helpers.group_chats import GroupChatHandler


@patch("messenger.helpers.group_chats.GroupChatHandler._get_record")
def test_is_user_in_group_chat(
    _get_record_mock: MagicMock, mocker: MockerFixture
):
    group_chat_handler = GroupChatHandler(mocker.MagicMock())

    group_chat = GroupChatSchema(group_chat_id=21)
    _get_record_mock.return_value = group_chat

    is_in_group_chat = group_chat_handler.is_user_in_group_chat(
        group_chat.group_chat_id, UserSchema(user_id=1)
    )

    _get_record_mock.assert_called_once()

    assert is_in_group_chat is True

    _get_record_mock.return_value = None

    is_in_group_chat = group_chat_handler.is_user_in_group_chat(
        group_chat.group_chat_id, UserSchema(user_id=1)
    )

    assert is_in_group_chat is False


@pytest.mark.parametrize(
    "criterion",
    [
        ((GroupChatSchema.group_chat_id == 3)),
        (
            (
                GroupChatSchema.group_chat_id == 122,
                GroupChatSchema.name == "group-chat23",
            )
        ),
        ((GroupChatSchema.name == "a-groupchat_name",)),
    ],
)
@patch(
    "messenger.helpers.group_chats.GroupChatHandler._get_record_with_not_found_raise"
)
def test_get_group_chat(
    _get_record_with_not_found_raise_mock: MagicMock,
    mocker: MockerFixture,
    criterion,
):
    group_chat_handler = GroupChatHandler(mocker.MagicMock())

    expected_group_chat = GroupChatSchema(group_chat_id=21)
    _get_record_with_not_found_raise_mock.return_value = expected_group_chat

    group_chat = group_chat_handler.get_group_chat(criterion)

    _get_record_with_not_found_raise_mock.assert_called_once_with(
        GroupChatSchema, "no such group chat exists", criterion
    )

    assert group_chat is expected_group_chat
    assert group_chat_handler.group_chat is expected_group_chat
