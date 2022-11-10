from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import pytest
from fastapi import HTTPException
from pytest_mock import MockerFixture
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import FriendshipSchema

from _submodules.messenger_utils.messenger_schemas.schema.user_schema import \
    UserSchema
from messenger.helpers.db import (get_record, get_record_with_not_found_raise,
                                  get_records)

test_password_hash="some-hash"

test_params = [
        (UserSchema, UserSchema.username == 'username'), 
        (UserSchema, UserSchema.first_name == "first name"), 
        (FriendshipSchema, [FriendshipSchema.addressee_id == 1, FriendshipSchema.requester_id > 12])]

class TestGetRecords:
    def test_returns_none(self, mocker: MockerFixture):
        session_mock = mocker.MagicMock()
        
        session_mock.query.return_value.filter.return_value = []
        record = get_records(session_mock, UserSchema, UserSchema.user_id > 5)
        assert record is None

    @pytest.mark.parametrize("Schema,criterion", test_params)
    def test_retrieves_records_successfully(self, mocker: MockerFixture, Schema, criterion):
        session_mock = mocker.MagicMock()
        
        # we mock that the filter function returns a tuple (in reality it returns a Query type, but we only need to test that it converts to list)
        filter_return = ('value_1', 'value_2', 'some other value')
        
        # the expected return should be a list object
        expected_return = list(filter_return)
        
        # filter will return a tuple
        session_mock.query.return_value.filter.return_value = expected_return
        
        retrieved_records = get_records(session_mock, Schema, criterion)
        
        session_mock.query.assert_called_once_with(Schema)
        session_mock.query.return_value.filter.assert_called_once_with(criterion)
        
        assert(len(retrieved_records) == len(expected_return))
        
        assert retrieved_records == expected_return

class TestGetRecord:
    @pytest.mark.parametrize("Schema,criterion", test_params)
    def test_retrieves_successfully(self, mocker: MockerFixture, Schema, criterion):
        session_mock = mocker.MagicMock()
        
        expected_user = UserSchema(user_id=1, username="user_3", password_hash=test_password_hash, email="email_3")
        session_mock.query.return_value.filter.return_value.one.return_value = expected_user
        
        record = get_record(session_mock, Schema, criterion)
        
        session_mock.query.assert_called_once_with(Schema)
        session_mock.query.return_value.filter.assert_called_once_with(criterion)
        session_mock.query.return_value.filter.return_value.one.assert_called_once()
        
        assert record == expected_user


    def test_returns_none(self, mocker: MockerFixture):
        session_mock = mocker.MagicMock()
        
        # if a NoResultFound error is given it should return None
        session_mock.query.return_value.filter.return_value.one.side_effect = NoResultFound()
        record = get_record(session_mock, UserSchema, UserSchema.username=='username')
        assert record is None

    def test_raises_on_multiple_found(self, mocker: MockerFixture):
        session_mock = mocker.MagicMock()
        
        session_mock.query.return_value.filter.return_value.one.side_effect = MultipleResultsFound()
        
        with pytest.raises(HTTPException):
            get_record(session_mock, UserSchema, UserSchema.password_hash=='some-password-hash')


class TestGetRecordWithNotFoundRaise:
    @pytest.mark.parametrize("Schema,criterion", test_params)
    def test_retrieves_successfully(self, mocker: MockerFixture, Schema, criterion):
        session_mock = mocker.MagicMock()
        
        expected_user = UserSchema(user_id=1, username="user_3", password_hash=test_password_hash, email="email_3")
        session_mock.query.return_value.filter.return_value.one.return_value = expected_user
        
        # should be able to get records of all test users now that they have been added to db
        record = get_record_with_not_found_raise(session_mock, Schema, "some detail", criterion)
        
        session_mock.query.assert_called_once_with(Schema)
        session_mock.query.return_value.filter.assert_called_once_with(criterion)
        
        assert record == expected_user


    def test_raises_when_none_found(self, mocker: MockerFixture):
        session_mock = mocker.MagicMock()
        
        session_mock.query.return_value.filter.return_value.one.side_effect = NoResultFound()
        
        with pytest.raises(HTTPException):
            get_record_with_not_found_raise(session_mock, UserSchema, "some detail", UserSchema.username=='username')


    def test_raises_on_multiple_found(self, mocker: MockerFixture):
        session_mock = mocker.MagicMock()
        
        session_mock.query.return_value.filter.return_value.one.side_effect = MultipleResultsFound()
        
        with pytest.raises(HTTPException):
            get_record_with_not_found_raise(session_mock, UserSchema, "some detail", UserSchema.username=='username')