from datetime import datetime
from fastapi import HTTPException
from freezegun import freeze_time

import pytest
from _submodules.messenger_utils.messenger_schemas.schema.friendship_schema import FriendshipSchema
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_schema import FriendshipStatusSchema
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from sqlalchemy.orm import Session
from messenger.constants.friendship_status_codes import FriendshipStatusCode

from messenger.helpers.friends import address_friendship_request, get_latest_friendship_status, raise_if_blocked
from tests.conftest import add_initial_friendship_status_codes

# the date that the initial records will be added at
INITIAL_RECORDS_DATE = '2022-11-06'
ONE_DAY_AFTER = '2022-11-07'

@pytest.fixture
@freeze_time(INITIAL_RECORDS_DATE)
def get_records(session: Session) -> tuple[Session, UserSchema, UserSchema, FriendshipSchema, FriendshipStatusSchema]:
    add_initial_friendship_status_codes(session)
    
    requester = UserSchema(username="user_1", password_hash="pass-hash", email="email_1")
    addressee = UserSchema(username="user_2", password_hash="pass-hash", email="email_2")
    
    session.add(requester)
    session.add(addressee)
    
    session.commit()
    
    friendship = FriendshipSchema(requester_id=requester.user_id, addressee_id=addressee.user_id, created_date_time=datetime.now())
    status = FriendshipStatusSchema(
        requester_id=requester.user_id,
        addressee_id=addressee.user_id,
        specified_date_time=datetime.now(),
        status_code_id=FriendshipStatusCode.REQUESTED.value,
        specifier_id=requester.user_id)
    
    session.add(friendship)
    session.add(status)
    
    session.commit()
    
    return (session, requester, addressee, friendship, status)

@freeze_time(ONE_DAY_AFTER)
def test_get_latest_friendship_status(get_records: tuple[Session, UserSchema, UserSchema, FriendshipSchema, FriendshipStatusSchema]):
    (session, requester, addressee, friendship, status) = get_records
    
    latest_status = get_latest_friendship_status(friendship)
    
    assert latest_status == status
    
    # the new status will be added 1 day after the initial one was added
    status = FriendshipStatusSchema(
        requester_id=requester.user_id,
        addressee_id=addressee.user_id,
        specified_date_time=datetime.now(),
        status_code_id=FriendshipStatusCode.ACCEPTED.value,
        specifier_id=addressee.user_id)
    
    session.add(status)
    session.commit()
    
    latest_status = get_latest_friendship_status(friendship)
    
    assert latest_status == status

@freeze_time(ONE_DAY_AFTER)
def test_raise_if_blocked(get_records: tuple[Session, UserSchema, UserSchema, FriendshipSchema, FriendshipStatusSchema]):
    (session, requester, addressee, friendship, status) = get_records
    
    # should run without raising since friendship is initialized with requested status
    raise_if_blocked(friendship)
    
    status = FriendshipStatusSchema(
        requester_id=requester.user_id,
        addressee_id=addressee.user_id,
        specified_date_time=datetime.now(),
        status_code_id=FriendshipStatusCode.BLOCKED.value,
        specifier_id=addressee.user_id)
    
    session.add(status)
    session.commit()
    
    # should raise now that the friendship has a new status with a blocked status code
    with pytest.raises(HTTPException):
        raise_if_blocked(friendship)


class TestAddressFriendshipRequest:
    @freeze_time(ONE_DAY_AFTER)
    def test_it_adds_new_accepted_status(self, session: Session, get_records: tuple[Session, UserSchema, UserSchema, FriendshipSchema, FriendshipStatusSchema]):
        (session, requester, addressee, _, _) = get_records
        new_status = address_friendship_request(session, requester.username, addressee, FriendshipStatusCode.ACCEPTED)
        
        assert new_status.status_code_id == FriendshipStatusCode.ACCEPTED.value
    
    
    @freeze_time(ONE_DAY_AFTER)
    def test_it_adds_new_declined_status(self, session: Session, get_records: tuple[Session, UserSchema, UserSchema, FriendshipSchema, FriendshipStatusSchema]):
        (session, requester, addressee, _, _) = get_records
        new_status = address_friendship_request(session, requester.username, addressee, FriendshipStatusCode.DECLINED)
        
        assert new_status.status_code_id == FriendshipStatusCode.DECLINED.value
    
    @freeze_time(ONE_DAY_AFTER)
    def test_new_added_status_is_latest(self, session: Session, get_records: tuple[Session, UserSchema, UserSchema, FriendshipSchema, FriendshipStatusSchema]):
        (session, requester, addressee, friendship, status) = get_records
        new_status = address_friendship_request(session, requester.username, addressee, FriendshipStatusCode.ACCEPTED)
        latest_status = get_latest_friendship_status(friendship)
        
        assert latest_status != status
        assert latest_status == new_status
    
    
    def test_it_raises_when_no_requester_exists(self, session, get_records: tuple[Session, UserSchema, UserSchema, FriendshipSchema, FriendshipStatusSchema]):
        (session, _, addressee, _, _) = get_records
        
        with pytest.raises(HTTPException):
            address_friendship_request(session, "non-existent-requester", addressee, FriendshipStatusCode.ACCEPTED)
    
    
    def test_it_raises_when_no_friendship_exists(self, session):
        requester = UserSchema(username="user_1", password_hash="pass-hash", email="email_1")
        addressee = UserSchema(username="user_2", password_hash="pass-hash", email="email_2")
        
        session.add(requester)
        session.add(addressee)
        
        session.commit()
        
        with pytest.raises(HTTPException):
            address_friendship_request(session, requester.username, addressee, FriendshipStatusCode.ACCEPTED)
            
    def test_it_raises_when_friendship_blocked(self, session, get_records: tuple[Session, UserSchema, UserSchema, FriendshipSchema, FriendshipStatusSchema]):
        (session, requester, addressee, _, status) = get_records
        
        status.status_code_id=FriendshipStatusCode.BLOCKED.value
        
        with pytest.raises(HTTPException):
            address_friendship_request(session, requester.username, addressee, FriendshipStatusCode.ACCEPTED)

    
    def test_it_raises_when_friendship_addressed(self, session, get_records: tuple[Session, UserSchema, UserSchema, FriendshipSchema, FriendshipStatusSchema]):
        (session, requester, addressee, _, status) = get_records
        
        status.status_code_id=FriendshipStatusCode.ACCEPTED.value
        
        with pytest.raises(HTTPException):
            address_friendship_request(session, requester.username, addressee, FriendshipStatusCode.ACCEPTED)
        
        status.status_code_id=FriendshipStatusCode.DECLINED.value
        
        with pytest.raises(HTTPException):
            address_friendship_request(session, requester.username, addressee, FriendshipStatusCode.ACCEPTED)