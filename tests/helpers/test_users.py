from fastapi import HTTPException
import pytest
from sqlalchemy.orm import Session
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.environment_variables import JWT_SECRET
from messenger.helpers.auth import ALGORITHM, TokenData
from messenger.helpers.users import create_user, get_current_user
from jose import jwt

valid_usernames = ["hi_iamusername", "some_other_username", "bob231", "hellothere2"]
invalid_usernames = ["_invalid", "bob__23", "tim#2", "a", "this_username_is_way_too_long_to_be_acceptable"]

valid_passwords = ["AValidPassword23", "AnotherValid23Password", "23Valid**Pass", "//Valid/'Pass2332"]
invalid_passwords = ["Test1ng", "notavalidpassword23", "notAvalidpassword", "23322122awds", "invalidpassword", "23212", "NOTVALID"]

valid_emails = ["email@email.com", "something@email.com", "my.ownsite@ourearth.org", "aperson@gmail.com"]
invalid_emails = ['@email.com', "cool.cool", "not an email", "google.email@com"]

class TestCreateUser:
    def test_with_invalid_password(self, session: Session):
        for invalid_password in invalid_passwords:
            with pytest.raises(HTTPException):
                create_user(session, invalid_password, valid_emails[0], valid_usernames[0])


    def test_with_invalid_emails(self, session: Session):
        for invalid_email in invalid_emails:
            with pytest.raises(HTTPException):
                create_user(session, valid_passwords[0], invalid_email, valid_usernames[0])


    def test_with_invalid_username(self, session: Session):
        for invalid_username in invalid_usernames:
            with pytest.raises(HTTPException):
                create_user(session, valid_passwords[0], valid_emails[0], invalid_username)

    def test_it_fails_on_existent_username(self, session: Session):
        create_user(session, valid_passwords[0], valid_emails[0], valid_usernames[0])
        
        with pytest.raises(HTTPException):
                create_user(session, valid_passwords[1], valid_emails[1], valid_usernames[0])


    def test_it_fails_on_existent_email(self, session: Session):
        create_user(session, valid_passwords[0], valid_emails[0], valid_usernames[0])
        
        with pytest.raises(HTTPException):
                create_user(session, valid_passwords[1], valid_emails[0], valid_usernames[1])


    def test_it_adds_user_to_db(self, session: Session):
        for password, email, username in zip(valid_passwords, valid_emails, valid_usernames):
            created_user = create_user(session, password, email, username)
            
            expected_user = session.query(UserSchema).filter(UserSchema.user_id == created_user.user_id).one()
            
            assert expected_user == created_user