from fastapi import HTTPException
import pytest
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema.friendship_status_code_schema import FriendshipStatusCodeSchema
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.helpers.db import get_record, get_records, get_record_with_not_found_raise

test_password_hash="some-hash"

def get_test_records() -> tuple[list[UserSchema], list[FriendshipStatusCodeSchema]]:
    test_users = [
        UserSchema(username="user_1", password_hash=test_password_hash, email="email_1"),
        UserSchema(username="user_2", password_hash=test_password_hash, email="email_2"),
        UserSchema(username="user_3", password_hash=test_password_hash, email="email_3")
    ]

    test_friendship_status_codes = [
        FriendshipStatusCodeSchema(status_code_id="R", name="Requested"),
        FriendshipStatusCodeSchema(status_code_id="A", name="Accepted"),
        FriendshipStatusCodeSchema(status_code_id="D", name="Declined"),
    ]
    
    return test_users, test_friendship_status_codes

@pytest.fixture
def get_test_records_fixture() -> tuple[list[UserSchema], list[FriendshipStatusCodeSchema]]:
    return get_test_records()


def get_test_records_parameterized():
    (test_users, test_friendship_status_codes) = get_test_records()
    return zip(test_users, test_friendship_status_codes)


def test_get_records(session: Session, get_test_records_fixture: tuple[list[UserSchema], list[FriendshipStatusCodeSchema]]):
    (test_users, _) = get_test_records_fixture
    
    # no users should be retrievable yet therefore it should be None
    retrieved_users = get_records(session, UserSchema, UserSchema.password_hash==test_password_hash)
    assert retrieved_users is None
    
    # add users to db
    session.add_all(test_users)
    session.commit()
    
    # now that users have been added to db we should be able to retrieve the users
    retrieved_users = get_records(session, UserSchema, UserSchema.password_hash==test_password_hash)
    assert retrieved_users is not None
    assert(len(retrieved_users) == len(test_users))
    
    # verify that the retrieved users are indeed the correct ones
    for test_user, retrieved_record in zip(test_users, retrieved_users):
        session.refresh(test_user)
        
        assert retrieved_record == test_user
    
    # should return none if it cannot find a user
    retrieved_users = get_records(session, UserSchema, UserSchema.email=="non-existent-email")
    assert retrieved_users is None


class TestGetRecord:
    @pytest.mark.parametrize("test_user,test_friendship_status_code", get_test_records_parameterized())
    def test_it_retrieves_successfully(self, session: Session, test_user: UserSchema, test_friendship_status_code: FriendshipStatusCodeSchema):
        # nothing has been added to db yet so should be None
        retrieved_user = get_record(session, UserSchema, UserSchema.username==test_user.username)
        assert retrieved_user is None
        
        # add test users to database
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        
        # should be able to get records of all test users now that they have been added to db
        retrieved_user = get_record(session, UserSchema, UserSchema.username==test_user.username)
        
        assert retrieved_user == test_user
        
        
        # no friendship status code has been added to db yet so should be None
        retrieved_status_code = get_record(session, FriendshipStatusCodeSchema, FriendshipStatusCodeSchema.status_code_id==test_friendship_status_code.status_code_id)
        assert retrieved_status_code is None
        
        # add test friendship status codes to db
        session.add(test_friendship_status_code)
        session.commit()
        session.refresh(test_friendship_status_code)
        
        # should be able to get records of all test friendship status codes now that they have been added to db
        retrieved_status_code = get_record(session, FriendshipStatusCodeSchema, FriendshipStatusCodeSchema.status_code_id==test_friendship_status_code.status_code_id)
        
        assert retrieved_status_code == test_friendship_status_code
        
        # should return none if no record is found
        retrieved_user = get_record(session, UserSchema, UserSchema.username=="non-existent-user")
        assert retrieved_user is None


    def test_it_raises_on_multiple_found(self, session: Session, get_test_records_fixture: tuple[list[UserSchema], list[FriendshipStatusCodeSchema]]):
        (test_users, _) = get_test_records_fixture

        session.add_all(test_users)
        session.commit()
        
        with pytest.raises(HTTPException):
            get_record(session, UserSchema, UserSchema.password_hash==test_password_hash)


class TestGetRecordWithNotFoundRaise:
    @pytest.mark.parametrize("test_user,test_friendship_status_code", get_test_records_parameterized())
    def test_it_retrieves_successfully(self, session: Session, test_user: UserSchema, test_friendship_status_code: FriendshipStatusCodeSchema):    
        # nothing has been added to db yet so should raise exception when fetching record
        with pytest.raises(HTTPException):
            retrieved_user = get_record_with_not_found_raise(session, UserSchema, "some detail", UserSchema.username==test_user.username)

        
        # add test users to database
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        
        # should be able to get records of all test users now that they have been added to db
        retrieved_user = get_record_with_not_found_raise(session, UserSchema, "some detail", UserSchema.username==test_user.username)
        
        assert retrieved_user == test_user
        
        
        # no friendship status code has been added to db yet so should raise exception on fetch
        with pytest.raises(HTTPException):
            retrieved_status_code = get_record_with_not_found_raise(
                session, 
                FriendshipStatusCodeSchema,
                "some detail", 
                FriendshipStatusCodeSchema.status_code_id == test_friendship_status_code.status_code_id
            )
        
        # add test friendship status codes to db
        session.add(test_friendship_status_code)
        session.commit()
        session.refresh(test_friendship_status_code)
        
        # should be able to get records of all test friendship status codes now that they have been added to db
        retrieved_status_code = get_record_with_not_found_raise(
            session, 
            FriendshipStatusCodeSchema, 
            "some detail", 
            FriendshipStatusCodeSchema.status_code_id == test_friendship_status_code.status_code_id
        )
        
        assert retrieved_status_code == test_friendship_status_code
        
        # should raise exception if no record is found
        with pytest.raises(HTTPException):
            retrieved_user = get_record_with_not_found_raise(session, UserSchema, "some detail", UserSchema.username=="non-existent-user")


    def test_it_raises_on_multiple_found(self, session: Session, get_test_records_fixture: tuple[list[UserSchema], list[FriendshipStatusCodeSchema]]):
        (test_users, _) = get_test_records_fixture

        session.add_all(test_users)
        session.commit()
        
        with pytest.raises(HTTPException):
            get_record_with_not_found_raise(session, UserSchema, UserSchema.password_hash==test_password_hash)