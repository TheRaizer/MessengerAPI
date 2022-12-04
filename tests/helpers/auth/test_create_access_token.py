from datetime import datetime, timedelta
from typing import Any
from freezegun import freeze_time
import pytest
from jose import ExpiredSignatureError, JWTError, jwt
from messenger.environment_variables import JWT_SECRET
from messenger.helpers.auth.auth_token import (
    ALGORITHM,
    create_access_token,
)

from tests.helpers.auth import test_datas, test_time_deltas


class TestCreateAccessToken:
    @freeze_time("2022-11-06")
    @pytest.mark.parametrize("test_data", test_datas)
    def test_create_access_token(self, test_data: dict[str, Any]):
        # test WITH NO given expires_delta param
        copy_data = test_data.copy()

        # create token
        access_token = create_access_token(test_data)

        # decode token
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])

        # payload should have an exp property added to the original test_data
        expected_expire = int(
            (datetime.utcnow() + timedelta(minutes=15)).timestamp()
        )
        copy_data.update({"exp": expected_expire})

        assert payload == copy_data

        with pytest.raises(JWTError):
            jwt.decode(
                access_token, JWT_SECRET + "-invalid", algorithms=[ALGORITHM]
            )

    @freeze_time("2022-11-06")
    @pytest.mark.parametrize(
        "test_data,test_time_delta", zip(test_datas, test_time_deltas)
    )
    def test_create_access_token_with_time_delta(
        self, test_data: dict[str, Any], test_time_delta: timedelta
    ):

        # test WITH a given expires_delta param
        copy_data = test_data.copy()

        access_token = create_access_token(test_data, test_time_delta)

        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])

        # payload should have an exp property added to the original test_data
        expected_expire = int((datetime.utcnow() + test_time_delta).timestamp())
        copy_data.update({"exp": expected_expire})

        assert payload == copy_data

        with pytest.raises(JWTError):
            jwt.decode(
                access_token, JWT_SECRET + "-invalid", algorithms=[ALGORITHM]
            )

    def test_create_access_token_expires(self):
        # set expires delta to a negative value
        access_token = create_access_token(test_datas[0], timedelta(days=-10))

        # the access token should therefore be expired
        with pytest.raises(ExpiredSignatureError):
            jwt.decode(access_token, JWT_SECRET, algorithms=[ALGORITHM])
