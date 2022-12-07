from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.orm import Session
from pytest_mock import MockerFixture
from _submodules.messenger_utils.messenger_schemas.schema.group_chat_member_schema import (
    GroupChatMemberSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.group_chat_schema import (
    GroupChatSchema,
)
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.helpers.group_chats import GroupChatHandler


@pytest.mark.parametrize(
    "user_id, group_chat_id",
    [(1, 3), (4, 2), (12, 1223), (11, 93), (98, 11)],
)
class TestIsUserInGroupChat:
    def test_when_true(
        self, user_id: int, group_chat_id: int, session: Session
    ):
        group_chat_handler = GroupChatHandler(session)

        user = UserSchema(
            user_id=user_id,
            username="username",
            email="email",
            password_hash="password_hash",
        )
        group_chat = GroupChatSchema(name="name", group_chat_id=group_chat_id)

        insert_stmnt = GroupChatMemberSchema.insert().values(
            group_chat_id=group_chat.group_chat_id, member_id=user.user_id
        )

        session.add(user)
        session.add(group_chat)
        session.commit()

        session.execute(insert_stmnt)
        session.commit()

        is_in_group_chat = group_chat_handler.is_user_in_group_chat(
            group_chat.group_chat_id, user.user_id
        )

        assert is_in_group_chat is True

    def test_when_false(
        self, user_id: int, group_chat_id: int, session: Session
    ):
        group_chat_handler = GroupChatHandler(session)

        user = UserSchema(
            user_id=user_id,
            username="username",
            email="email",
            password_hash="password_hash",
        )
        other_user = UserSchema(
            user_id=user_id + 1,
            username="other_username",
            email="other_email",
            password_hash="password_hash",
        )
        group_chat = GroupChatSchema(name="name", group_chat_id=group_chat_id)

        insert_stmnt = GroupChatMemberSchema.insert().values(
            group_chat_id=group_chat.group_chat_id, member_id=other_user.user_id
        )

        session.add(user)
        session.add(other_user)
        session.add(group_chat)
        session.commit()

        session.execute(insert_stmnt)
        session.commit()

        is_in_group_chat = group_chat_handler.is_user_in_group_chat(
            group_chat.group_chat_id, user.user_id
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
