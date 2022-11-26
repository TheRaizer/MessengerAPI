
def is_password_valid(password: str) -> bool:
    """Verifies whether a password is valid.

    Args:
        password (str): Password to verify.

    Returns:
        bool: whether the password is valid.
    """
    rules = [
        lambda password: any(
            char.isupper() for char in password
        ),  # must have at least one uppercase
        lambda password: any(
            char.islower() for char in password
        ),  # must have at least one lowercase
        lambda password: any(
            char.isdigit() for char in password
        ),  # must have at least one digit
        lambda password: len(password) >= 8,  # must be at least 8 characters
    ]

    # apply each rule to the password and ensure that all are true
    if all(rule(password) for rule in rules):
        return True

    return False

