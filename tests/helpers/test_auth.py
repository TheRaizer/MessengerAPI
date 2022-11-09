from freezegun import freeze_time
from datetime import datetime, timedelta

import pytest
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import UserSchema
from messenger.environment_variables import JWT_SECRET
from messenger.helpers.auth import ALGORITHM, LOGIN_TOKEN_EXPIRE_MINUTES, TokenData, create_access_token, create_login_token
from jose import ExpiredSignatureError, JWTError, jwt

test_datas = [
    { "key_1": 1, "key_2": "some-value" },
    { "hello": { "key": "value" }, "world": -23 },
    { "obj": { "val": 23, "other_val": { "foo": "bar" }}, "other_obj": { "test": ["test", "list"] }}
]

class TestCreateAccessToken:
    @freeze_time('2022-11-06')
    def test_create_access_token(self):
        # test WITH NO given expires_delta param
        for test_data in test_datas:
            copy_data = test_data.copy()
            
            # create token
            access_token = create_access_token(test_data)
            
            # decode token
            payload = jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])
            
            # payload should have an exp property added to the original test_data
            expected_expire = int((datetime.utcnow() + timedelta(minutes=15)).timestamp())
            copy_data.update({ "exp": expected_expire })
            
            assert payload == copy_data
            
            with pytest.raises(JWTError):
                jwt.decode(access_token, JWT_SECRET + "-invalid", algorithms=[ALGORITHM])


    @freeze_time('2022-11-06')
    def test_create_access_token_with_time_delta(self):
        test_time_deltas = [
            timedelta(days=1),
            timedelta(seconds=4),
            timedelta(minutes=0.8)
        ]
        
        # test WITH a given expires_delta param
        for test_data, test_time_delta in zip(test_datas, test_time_deltas):
            copy_data = test_data.copy()
            
            access_token = create_access_token(test_data, test_time_delta)
            
            payload = jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])
            
            # payload should have an exp property added to the original test_data
            expected_expire = int((datetime.utcnow() + test_time_delta).timestamp())
            copy_data.update({ "exp": expected_expire })
            
            assert payload == copy_data
            
            with pytest.raises(JWTError):
                jwt.decode(access_token, JWT_SECRET + "-invalid", algorithms=[ALGORITHM])


    def test_create_access_token_expires(self):
        # set expires delta to a negative value
        access_token = create_access_token(test_datas[0], timedelta(days=-10))
        
        # the access token should therefore be expired
        with pytest.raises(ExpiredSignatureError):
            jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])


@freeze_time('2022-11-06')
def test_create_login_token():
    test_user_records = [
        UserSchema(username="user_1", password_hash="hash_1", email="email_1"),
        UserSchema(username="user_2", password_hash="hash_2", email="email_2"),
        UserSchema(username="user_3", password_hash="hash_3", email="email_3")
    ]
    
    for test_user_record in test_user_records:
        # generate login token for the user
        login_token = create_login_token(test_user_record)
        
        # the expected expirey should use the LOGIN_TOKEN_EXPIRE_MINUTES constant
        expected_expire = int((datetime.utcnow() + timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES)).timestamp())
        
        # here we generate the expected token data
        expected_token_data = TokenData(user_id=test_user_record.user_id, username=test_user_record.username, email=test_user_record.email).dict()
        expected_token_data.update({ "exp": expected_expire })
        
        # decode the payload
        payload = jwt.decode(login_token, JWT_SECRET, algorithms=[ALGORITHM])
        
        assert payload == expected_token_data
        
        with pytest.raises(JWTError):
            jwt.decode(login_token, JWT_SECRET + "-invalid", algorithms=[ALGORITHM])