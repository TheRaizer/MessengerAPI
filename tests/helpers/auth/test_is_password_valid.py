import pytest
from messenger.helpers.auth.is_password_valid import is_password_valid

from tests.conftest import (
    valid_passwords,
    invalid_passwords,
)


class TestIsPasswordValid:
    @pytest.mark.parametrize(
        "password",
        valid_passwords,
    )
    def test_valid_password(self, password: str):
        is_valid = is_password_valid(password)
        assert is_valid is True

    @pytest.mark.parametrize(
        "password",
        invalid_passwords,
    )
    def test_invalid_password(self, password: str):
        is_valid = is_password_valid(password)
        assert is_valid is False
