from datetime import datetime, timedelta
from freezegun import freeze_time
import pytest
from jose import JWTError, jwt
from _submodules.messenger_utils.messenger_schemas.schema.user_schema import (
    UserSchema,
)
from messenger.environment_variables import JWT_SECRET
from messenger.helpers.auth.auth_token import (
    ALGORITHM,
    LOGIN_TOKEN_EXPIRE_MINUTES,
    TokenData,
    create_login_token,
)
from tests.helpers.auth import test_user_records


@freeze_time("2022-11-06")
@pytest.mark.parametrize("test_user_record", test_user_records)
def test_create_login_token(test_user_record: UserSchema):
    # generate login token for the user
    login_token = create_login_token(test_user_record)

    # the expected expiry should use the LOGIN_TOKEN_EXPIRE_MINUTES constant
    expected_expire = int(
        (
            datetime.utcnow() + timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES)
        ).timestamp()
    )

    # here we generate the expected token data
    expected_token_data = TokenData(
        user_id=test_user_record.user_id,
        username=test_user_record.username,
        email=test_user_record.email,
    ).dict()
    expected_token_data.update({"exp": expected_expire})

    # decode the payload
    payload = jwt.decode(login_token, JWT_SECRET, algorithms=[ALGORITHM])

    assert payload == expected_token_data

    with pytest.raises(JWTError):
        jwt.decode(login_token, JWT_SECRET + "-invalid", algorithms=[ALGORITHM])
